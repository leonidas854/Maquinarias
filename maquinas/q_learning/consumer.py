import json
from datetime import datetime
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify
from .Services.rl_service import RLModelManager
from Reportes.models import Lineas_Embotelladoras
from q_learning.models import Simulacion_estado
from q_learning.Services.ServicesQ_learning_ import ServicesQ_learning
from channels.generic.websocket import AsyncWebsocketConsumer
from Markov.Services.ServicesMarkov_ import ServicesMarkov

class MaquinaConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.linea_nombre = self.scope['url_route']['kwargs']['nombre_linea']
        safe_group_name = slugify(self.linea_nombre)
        self.room_group_name = f'maquina_{safe_group_name}'
        self.user = self.scope.get('user', None)

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"WebSocket conectado para la línea: {self.linea_nombre} por el usuario: {self.user}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"WebSocket desconectado de la línea: {self.linea_nombre}")

    async def receive(self, text_data):

        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'realtime_update':
                await self.handle_realtime_prediction(data.get('payload', {}))
            elif message_type == 'decision_confirmada':
                await self.handle_decision_confirmada(data.get('payload', {}))
            else:
                await self.send_error(f"Tipo de mensaje desconocido: {message_type}")

        except json.JSONDecodeError:
            await self.send_error("Mensaje no es un JSON válido.")
        except Exception as e:
            await self.send_error(f"Error inesperado en receive: {str(e)}")



    async def handle_realtime_prediction(self, payload):
        
        try:
            @sync_to_async
            def get_prediction_data(linea_nombre, payload_data):
                
                sim_temp = ServicesQ_learning(linea_nombre)
                estado_actual = ServicesMarkov(linea_nombre).get_ultimo_estado()
                nombre_estado_actual = estado_actual.get('estado')
                id_estado_actual = sim_temp.estado_invertido.get(nombre_estado_actual)
                datos_reales_originales = {"uso": float(payload_data['uso']),"temperatura": float(payload_data['temperatura']),"presion": float(payload_data['presion'])}
                obs = RLModelManager.normalizar_observacion(datos_reales_originales, linea_nombre, id_estado_actual)
                model = RLModelManager.get_model()
                action, _ = model.predict(obs, deterministic=True)
                recomendacion = RLModelManager.traducir_accion(int(action))
                estado_actual_dict = {'nombre': nombre_estado_actual, **datos_reales_originales}
                recompensa = self._calcular_recompensa_estimada(int(action), estado_actual_dict, sim_temp.linea_config)
                
                return {
                    "recomendacion": recomendacion,
                    "action_id": int(action),
                    "recompensa": recompensa,
                    "datos_sensor": datos_reales_originales,
                    "datos_modelo": datos_reales_originales
                }

            prediction_result = await get_prediction_data(self.linea_nombre, payload)
            
            
            response_data = {
                'type': 'realtime_recommendation',
                'recommendation': prediction_result["recomendacion"],
                'action_id': prediction_result["action_id"],
                'recompensa_estimada': round(prediction_result["recompensa"], 2),
                'datos_sensor': prediction_result['datos_sensor'],
                'datos_modelo': prediction_result['datos_modelo'],
                
            }
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_message', # Un nombre de handler diferente
                    'message': response_data
                }
            )
        except Exception as e:
            await self.send_error(f"Error en predicción en tiempo real: {str(e)}")

   
    async def broadcast_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps(message))


 

    @sync_to_async
    def crear_evento_preliminar(self, acc_ia, datos, recompensa):
        linea = Lineas_Embotelladoras.objects.get(Nombre=self.linea_nombre)
        
        usuario = self.user if self.user and self.user.is_authenticated else None

        evento = Simulacion_estado.objects.create(
            Linea_id=linea,
            Usuario_id=usuario,
            Fecha=timezone.now().date(),
            Acc_IA=acc_ia,
            Temperatura=datos['temperatura'],
            Presion=datos['presion'],
            Uso=datos['uso'],
            Recompensa=recompensa,
            Invervencion=False 
        )
        return evento.id

    async def handle_decision_confirmada(self, payload):
        """Actualiza el registro en `Simulacion_estado` con la decisión final."""
        try:
            evento_id = payload['evento_id']
            decision_humana = payload['decision'] # Ej: 'aceptada' o 'anulada'

            await self.actualizar_evento_final(evento_id, decision_humana, payload)
            
            await self.send_json({
                'type': 'decision_guardada',
                'status': 'ok',
                'message': f'Decisión para el evento {evento_id} guardada correctamente.'
            })
            
        except KeyError as e:
            await self.send_error(f"Falta el campo requerido '{e}' en el payload de confirmación.")
        except Exception as e:
            await self.send_error(f"Error al confirmar la decisión: {str(e)}")

    @sync_to_async
    def actualizar_evento_final(self, evento_id, decision, payload):
        """Actualiza el registro en la BD con la acción final."""
        try:
            evento = Simulacion_estado.objects.get(id=evento_id)
            
            if decision == 'aceptada':
                evento.acc_final = evento.Acc_IA
                evento.Invervencion = False
            elif decision == 'anulada':
                accion_humana = payload.get('accion_humana', 'Anulación sin especificar')
                evento.Acc_humana = accion_humana
                evento.acc_final = accion_humana
                evento.Invervencion = True
                evento.Comentario = payload.get('comentario', '')
            else:
                raise ValueError("La decisión debe ser 'aceptada' o 'anulada'.")
            
            evento.save()
        except ObjectDoesNotExist:
            raise ValueError(f"No se encontró el evento con ID {evento_id}.")

    def _calcular_recompensa_estimada(self, action: int, estado_actual: dict, config: dict) -> float:
        reward = 0.0
        temp, pres, estado_nombre = estado_actual['temperatura'], estado_actual['presion'], estado_actual['nombre']
        temp_max, pres_max = config["Temp_max"], config["Presion_maxima"]
        
        if temp > temp_max * 0.9: reward -= 1.5 
        if pres > pres_max * 0.9: reward -= 1.5

        if estado_nombre == 'Operativa': reward += 1.0 
        elif estado_nombre in ['Mantenimiento', 'Parada']: reward -= 2.0 
       

        if action == 2 and estado_nombre == 'Operativa' and temp < temp_max * 0.9: reward -= 10
        if action == 2 and (temp > temp_max * 0.9 or pres > pres_max * 0.9): reward += 15 

        if temp > temp_max: reward -= 20
        if pres > pres_max: reward -= 20

        return reward

    async def send_json(self, data):
        await self.send(text_data=json.dumps(data))

    async def send_error(self, message):
        print(f"ERROR en WebSocket ({self.linea_nombre}): {message}")
        await self.send_json({'type': 'error', 'message': message})