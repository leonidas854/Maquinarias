import websocket
import json
import time
import random
import threading
import requests
import numpy as np
from urllib.parse import quote

DJANGO_SERVER_IP = "192.168.1.7"
LINEA_A_SIMULAR = "Línea k-128" 


class LineaSimulator:
    def __init__(self, config):
        self.config = config
        self.current_temp = config.get('Temp_min', 20)
        self.current_pres = config.get('Presion_base', 100)
        self.current_uso = 0
        self.estado_simulado = 'Operativa' 

    def _fourier_temp(self, t, amplitud):
      
        return amplitud * np.sin((2 * np.pi * t) / 24)

    def simular_siguiente_paso(self, t):
        target_uso = self.config['Uso_operativo'] if self.estado_simulado == 'Operativa' else 0
        self.current_uso += (target_uso - self.current_uso) * 0.1 + random.uniform(-2, 2)
        self.current_uso = np.clip(self.current_uso, 0, 100)

       
        temp_base = self.config['Temp_min']
        delta_uso = (self.current_uso / 100) * (self.config['Temp_max'] - temp_base)
        fourier = self._fourier_temp(t, 4.0) # Amplitud de 4 grados
        self.current_temp = temp_base + delta_uso + fourier + random.uniform(-0.5, 0.5)
        self.current_temp = np.clip(self.current_temp, temp_base - 5, self.config['Temp_max'] + 10)

    
        pres_base = self.config['Presion_base']
        target_pres = pres_base + 0.4 * self.current_temp + 0.3 * self.current_uso
        self.current_pres += (target_pres - self.current_pres) * 0.2 + random.uniform(-3, 3)
        self.current_pres = np.clip(self.current_pres, pres_base - 10, self.config['Presion_maxima'] + 15)

        return {
            "uso": self.current_uso,
            "temperatura": self.current_temp,
            "presion": self.current_pres
        }

    def aplicar_recomendacion(self, accion_id: int):
        """Ajusta el estado interno del simulador basado en la recomendación."""
        if accion_id == 2: # Mantenimiento
            self.estado_simulado = 'Mantenimiento'
            self.current_temp *= 0.95
            self.current_pres *= 0.90
        elif accion_id == 1: # Parada
            self.estado_simulado = 'Parada'
        elif accion_id == 0: # Operativa
            self.estado_simulado = 'Operativa'


def on_message(ws, message):
    data = json.loads(message)
    print(f"\n<-- MENSAJE RECIBIDO: {data}")

    if data.get('type') == 'realtime_recommendation':
        line_simulator.aplicar_recomendacion(data.get('action_id'))

def on_open(ws, line_simulator):
    """Inicia el bucle de envío de datos usando el simulador de línea."""
    print("### Conexión establecida. Iniciando simulación de sensores realista... ###")
    
    def run(*args):
        t = 0
        while True:
            try:
                sensor_data = line_simulator.simular_siguiente_paso(t)
                
                message_to_send = { "type": "realtime_update", "payload": sensor_data }
                ws.send(json.dumps(message_to_send))
                
                print(f"\n-> DATO ENVIADO (t={t}): "
                      f"Uso={sensor_data['uso']:.1f}%, "
                      f"Temp={sensor_data['temperatura']:.1f}°C, "
                      f"Pres={sensor_data['presion']:.1f}bar")
                
                t += 1
                time.sleep(3)
            except Exception as e:
                print(f"Error en el bucle de envío: {e}")
                break
    
    threading.Thread(target=run, daemon=True).start()

def get_config_from_django(server_ip, linea):
    """Función para obtener la configuración de la línea desde la API de Django."""
    api_url = f"http://{server_ip}:8000/qlearning/api/configuracion/?linea={linea}"
    try:
        print(f"Obteniendo configuración para '{linea}' desde {api_url}...")
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()  # Lanza un error si la respuesta es 4xx o 5xx
        config = response.json()
        print("Configuración recibida:", config)
        return config
    except requests.exceptions.RequestException as e:
        print(f"!!! ERROR: No se pudo obtener la configuración de Django: {e}")
        return None

if __name__ == "__main__":

    line_config = get_config_from_django(DJANGO_SERVER_IP, LINEA_A_SIMULAR)
    
    if line_config:

        line_simulator = LineaSimulator(line_config)

        linea_url_safe = quote(LINEA_A_SIMULAR)
        ws_url = f"ws://{DJANGO_SERVER_IP}:8000/ws/maquina/{linea_url_safe}/"

        ws_app = websocket.WebSocketApp(ws_url,
                                      on_open=lambda ws: on_open(ws, line_simulator),
                                      on_message=on_message,
                                      on_error=lambda ws, e: print(f"!!! Error: {e}"),
                                      on_close=lambda ws, sc, sm: print("### Conexión cerrada ###"))
        
        print(f"Intentando conectar a {ws_url}...")
        ws_app.run_forever()