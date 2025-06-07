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
                # 1. Inicializar el simulador (operación síncrona con acceso a BD)
                sim_temp = ServicesQ_learning(linea_nombre)
                
                # 2. Obtener estado actual (asumimos fallback por ahora)
                nombre_estado_actual = 'Operativa'
                id_estado_actual = sim_temp.estado_invertido.get(nombre_estado_actual)

                if id_estado_actual is None:
                    raise ValueError(f"El estado por defecto '{nombre_estado_actual}' no es válido.")

                # 3. Preparar datos y normalizar la observación
                datos_reales = {
                    "uso": float(payload_data['uso']),
                    "temperatura": float(payload_data['temperatura']),
                    "presion": float(payload_data['presion'])
                }
                obs = RLModelManager.normalizar_observacion(datos_reales, linea_nombre, id_estado_actual)

               
                model = RLModelManager.get_model()
                action, _ = model.predict(obs, deterministic=True)
                
                # 5. Traducir la acción y calcular la recompensa
                recomendacion = RLModelManager.traducir_accion(int(action))
                
                estado_actual_dict = {'nombre': nombre_estado_actual, **datos_reales}
                recompensa = self._calcular_recompensa_estimada(int(action), estado_actual_dict, sim_temp.linea_config)
                
                return {
                    "recomendacion": recomendacion,
                    "action_id": int(action),
                    "recompensa": recompensa
                }

            prediction_result = await get_prediction_data(self.linea_nombre, payload)
            
            await self.send_json({
                'type': 'realtime_recommendation',
                'recommendation': prediction_result["recomendacion"],
                'action_id': prediction_result["action_id"],
                'recompensa_estimada': round(prediction_result["recompensa"], 2)
            })

        except Exception as e:
            await self.send_error(f"Error en predicción en tiempo real: {str(e)}")

    @sync_to_async
    def crear_evento_preliminar(self, acc_ia, datos, recompensa):
        """Crea el registro en la BD de forma síncrona dentro de un wrapper asíncrono."""
        linea = Lineas_Embotelladoras.objects.get(Nombre=self.linea_nombre)
        
        # Manejo del usuario. Si no está autenticado, no se asigna.
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
            # Los campos de decisión humana se dejan nulos por ahora
            Invervencion=False # La intervención es falsa hasta que el humano diga lo contrario
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
        """Espejo de la función _get_reward del entorno."""
        # Esta es la misma lógica de recompensa que definimos antes
        reward = 0.0
        temp, pres, estado_nombre = estado_actual['temperatura'], estado_actual['presion'], estado_actual['nombre']
        temp_max, pres_max = config["Temp_max"], config["Presion_maxima"]
        
        # Penalización por operar en rangos peligrosos
        if temp > temp_max * 0.9: reward -= 1.5 
        if pres > pres_max * 0.9: reward -= 1.5

        # Recompensa/penalización por estado
        if estado_nombre == 'Operativa': reward += 1.0 
        elif estado_nombre in ['Mantenimiento', 'Parada']: reward -= 2.0 
       
        # Asumiendo que la acción 2 es la de mantenimiento
        if action == 2 and estado_nombre == 'Operativa' and temp < temp_max * 0.9: reward -= 10
        if action == 2 and (temp > temp_max * 0.9 or pres > pres_max * 0.9): reward += 15 

        # Penalización severa por exceder límites
        if temp > temp_max: reward -= 20
        if pres > pres_max: reward -= 20

        return reward

    async def send_json(self, data):
        await self.send(text_data=json.dumps(data))

    async def send_error(self, message):
        print(f"ERROR en WebSocket ({self.linea_nombre}): {message}")
        await self.send_json({'type': 'error', 'message': message})