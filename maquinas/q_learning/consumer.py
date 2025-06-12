# q_learning/consumers.py

import json
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify

from .Services.rl_service import RLModelManager
from Markov.Services.ServicesMarkov_ import ServicesMarkov
from Reportes.models import Lineas_Embotelladoras
from q_learning.models import Simulacion_estado
from .Services.ServicesQ_learning_ import ServicesQ_learning
from django.contrib.auth.models import User

class MaquinaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.linea_nombre = self.scope['url_route']['kwargs']['nombre_linea']
        self.room_group_name = f"maquina_{slugify(self.linea_nombre)}"
        self.user = self.scope.get("user")
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"WebSocket conectado para la línea: {self.linea_nombre}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"WebSocket desconectado de la línea: {self.linea_nombre}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'realtime_update':
                await self.handle_realtime_prediction(data.get('payload', {}))
            elif message_type == 'request_initial_state':
                await self.handle_request_initial_state()
       
            elif message_type == 'decision_confirmada':
                await self.handle_decision_confirmada(data.get('payload', {}))
            
            elif message_type == 'simulate_future':
                await self.handle_future_simulation(data.get('payload', {}))
            
            else:
                await self.send_error(f"Tipo de mensaje desconocido: {message_type}")
        except json.JSONDecodeError:
            await self.send_error("Error: El mensaje recibido no es un JSON válido.")
        except Exception as e:
            await self.send_error(f"Error inesperado en el servidor: {str(e)}")
            
    async def handle_future_simulation(self, payload):
        try:
            horas_a_simular = int(payload.get('horas', 24))
            print(f"  [Consumer] Iniciando simulación INTELIGENTE para '{self.linea_nombre}' por {horas_a_simular} horas.")

            @sync_to_async
            def run_intelligent_simulation(linea_nombre, horas):
  

                sim_service = ServicesQ_learning(linea_nombre)
                markov_service = ServicesMarkov(linea_nombre)
                model = RLModelManager.get_model()
                

                estado_info = markov_service.get_ultimo_estado()
                nombre_estado_actual = estado_info.get('estado', 'Operativa')
                id_estado_actual = sim_service.estado_invertido.get(nombre_estado_actual)

   
                initial_uso = sim_service.simular_uso(t=0, estado_id=id_estado_actual)
                initial_temp = sim_service.simular_temperatura(t=0, uso=initial_uso, estado_id=id_estado_actual)
                initial_pres = sim_service.simular_presion(temp=initial_temp, uso=initial_uso, estado_id=id_estado_actual)

                estado_simulado_actual = {
                    'id': id_estado_actual,
                    'nombre': nombre_estado_actual,
                    'uso': initial_uso,
                    'temperatura': initial_temp,
                    'presion': initial_pres
                }
                
                resultados = {'horas': [], 'uso': [], 'temperatura': [], 'presion': [], 'estados': []}

    
                for t in range(horas):
                
                    obs_simulada = RLModelManager.normalizar_observacion(
                        datos_reales=estado_simulado_actual, 
                        nombre_linea=linea_nombre,
                        nombre_estado_actual=estado_simulado_actual['nombre']
                    )

          
                    action_array, _ = model.predict(obs_simulada, deterministic=True)
                    action_id = int(action_array)

          
                    estado_simulado_siguiente = sim_service.simular_siguiente_paso(
                        t=t,
                        estado_actual=estado_simulado_actual,
                        accion_agente=action_id
                    )

              
                    resultados['horas'].append(t)
                    resultados['uso'].append(estado_simulado_siguiente['uso'])
                    resultados['temperatura'].append(estado_simulado_siguiente['temperatura'])
                    resultados['presion'].append(estado_simulado_siguiente['presion'])
                    resultados['estados'].append(estado_simulado_siguiente['nombre'])

                 
                    estado_simulado_actual = estado_simulado_siguiente
                
                return resultados

            simulation_data = await run_intelligent_simulation(self.linea_nombre, horas_a_simular)
            
        
            await self.send_json({
                'type': 'future_simulation_result',
                'simulation_data': simulation_data
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            await self.send_error(f"Error durante la simulación a futuro: {str(e)}")

    async def handle_request_initial_state(self):
        try:
            @sync_to_async
            def get_db_state(linea_nombre):
                markov_service = ServicesMarkov(linea_nombre)
                estado_info = markov_service.get_ultimo_estado()
                return estado_info.get('estado', 'Operativa') # Fallback seguro
            estado_real = await get_db_state(self.linea_nombre)
            await self.send_json({'type': 'initial_state_response', 'estado_real_maquina': estado_real})
        except Exception as e:
            await self.send_error(f"Error al obtener estado inicial: {str(e)}")

    async def handle_realtime_prediction(self, payload):

        try:
            @sync_to_async
            def get_prediction_data(linea_nombre, sensor_data):
                markov_service = ServicesMarkov(linea_nombre)
                estado_info = markov_service.get_ultimo_estado()
                nombre_estado_actual_real = estado_info.get('estado', 'Operativa')
                obs = RLModelManager.normalizar_observacion(sensor_data, linea_nombre, nombre_estado_actual_real)
                model = RLModelManager.get_model()
                action_array, _ = model.predict(obs, deterministic=True)
                action_id = int(action_array.item() if hasattr(action_array, 'item') else action_array)
                recomendacion_estado = RLModelManager.traducir_accion(action_id)
                recomendacion_desc = RLModelManager.traducir_accion_descripcion(action_id)
                estado_actual_dict = {'nombre': nombre_estado_actual_real, **sensor_data}
                config_completa = RLModelManager.get_linea_config(linea_nombre)
                recompensa = self._calcular_recompensa_estimada(action_id, estado_actual_dict, config_completa['linea_config_dict'])

                return {
                    "estado_real_maquina": nombre_estado_actual_real,
                    "recomendacion_estado": recomendacion_estado,
                    "recomendacion_desc": recomendacion_desc,     
                    "action_id": action_id,
                    "recompensa_estimada": recompensa,
                    "datos_sensor": sensor_data,
                }

            prediction_result = await get_prediction_data(self.linea_nombre, payload)
            
            response_data = {
                'type': 'realtime_recommendation',
                'estado_real_maquina': prediction_result["estado_real_maquina"],
                'recommendation': prediction_result["recomendacion_desc"],
                'recomendacion_estado': prediction_result["recomendacion_estado"],
                'recompensa_estimada': round(prediction_result["recompensa_estimada"], 2),
                'action_id': prediction_result["action_id"],
                'datos_sensor': prediction_result['datos_sensor'],
            }
            
        
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_realtime_recommendation', # Un nombre de método claro
                    'message': response_data
                }
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            await self.send_error(f"Error en predicción en tiempo real: {str(e)}")
    async def send_realtime_recommendation(self, event):
        
        message_to_send = event['message']
        message_to_send['type'] = 'realtime_recommendation'

        await self.send(text_data=json.dumps(message_to_send))

    async def handle_decision_confirmada(self, payload):

        try:
            await self.crear_y_guardar_evento_final(payload)
            
            
            
            await self.send_json({
                'type': 'decision_guardada',
                'status': 'ok',
                'message': f'Decisión "{payload["decision"]}" guardada correctamente.'
            })
        except KeyError as e:
            await self.send_error(f"Falta el campo requerido '{e}' en el payload de confirmación.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            await self.send_error(f"Error al confirmar la decisión: {str(e)}")

    @sync_to_async
    def crear_y_guardar_evento_final(self, payload: dict):
       
        decision = payload.get('decision')

    
        if decision != 'aceptada':
            print(f"  [Consumer] Decisión '{decision}' recibida. No se requiere acción de guardado.")
            return

     
        recomendacion_ia_desc = payload['recomendacion_ia']
        datos = payload['datos_sensor']
        recompensa = payload['recompensa_estimada']
        
        try:
            linea_obj = Lineas_Embotelladoras.objects.get(Nombre=self.linea_nombre)
        except Lineas_Embotelladoras.DoesNotExist:
            print(f"ERROR FATAL: No se pudo encontrar el objeto de línea para '{self.linea_nombre}'")
            return

        usuario_obj = self.user if self.user and self.user.is_authenticated else None
        
      
        action_id_ia = next((key for key, value in RLModelManager._accion_mapa.items() if value == recomendacion_ia_desc), 5)
        accion_ia_estado = RLModelManager.traducir_accion(action_id_ia)

       
        evento_data = {
            'Linea_id': linea_obj,
            'Usuario_id': usuario_obj,
            'Fecha': timezone.now(),
            'Acc_IA': accion_ia_estado,       
            'acc_final': accion_ia_estado,   
            'Invervencion': False,           
            'Temperatura': datos['temperatura'],
            'Presion': datos['presion'],
            'Uso': datos['uso'],
            'Recompensa': recompensa,
            'Acc_humana': None,            
            'Comentario': RLModelManager.traducir_accion_descripcion(action_id_ia)
        }

    
        Simulacion_estado.objects.create(**evento_data)
        print(f"  [Consumer] Evento ACEPTADO guardado en la BD para '{self.linea_nombre}'.")



    def _calcular_recompensa_estimada(self, action: int, estado_anterior: dict, config: dict) -> float:
      
        reward = 0.0
        estado_anterior_nombre = estado_anterior['nombre']
        temp_anterior = estado_anterior['temperatura']
        pres_anterior = estado_anterior['presion']
        temp_max = config.get("Temp_max", 90)
        pres_max = config.get("Presion_maxima", 150)
        estado_siguiente_nombre = RLModelManager.traducir_accion(action)

        if estado_siguiente_nombre == 'Operativa': reward += 5.0
        elif estado_siguiente_nombre in ['Parada', 'Mantenimiento']: reward -= 5.0
        elif estado_siguiente_nombre in ['Recuperación', 'Reserva']: reward -= 1.0

        if temp_anterior > temp_max * 0.8: reward -= 2.0 * ((temp_anterior - temp_max * 0.8) / (temp_max * 0.2))
        if pres_anterior > pres_max * 0.8: reward -= 2.0 * ((pres_anterior - pres_max * 0.8) / (pres_max * 0.2))

        if temp_anterior > temp_max: reward -= 20.0
        if pres_anterior > pres_max: reward -= 20.0

        if action != 5: reward -= 0.5
        if estado_siguiente_nombre != 'No Intervenir' and estado_siguiente_nombre == estado_anterior_nombre: reward -= 10.0

        is_healthy = (temp_anterior < temp_max * 0.8 and pres_anterior < pres_max * 0.8)
        if estado_anterior_nombre == 'Operativa' and is_healthy and action in [1, 2, 4]: reward -= 15.0

        is_at_risk = (temp_anterior > temp_max * 0.8 or pres_anterior > pres_max * 0.8)
        if is_at_risk and action == 2: reward += 20.0

        if estado_anterior_nombre in ['Mantenimiento', 'Parada', 'Recuperación'] and action == 0: reward += 10.0
            
        return reward

    async def send_json(self, data):
        await self.send(text_data=json.dumps(data))

    async def send_error(self, message):
        print(f"ERROR en WebSocket ({self.linea_nombre}): {message}")
        await self.send_json({'type': 'error', 'message': message})