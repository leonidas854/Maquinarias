# multisensor.py

import websocket
import json
import time
import random
import threading
import requests
import numpy as np
from urllib.parse import quote

# --- CONFIGURACIÓN ---
DJANGO_SERVER_IP = "192.168.1.10" # IP de tu servidor Django

class SensorSimulator:
    """
    Simula los sensores para UNA SOLA línea. Su estado interno solo cambia
    cuando el servidor le informa del estado inicial REAL. NO reacciona a recomendaciones.
    """
    def __init__(self, nombre_linea, config):
        self.nombre = nombre_linea
        self.config = config
        self.current_temp = config.get('Temp_min', 20)
        self.current_pres = config.get('Presion_base', 100)
        self.current_uso = 0
        self.estado_simulado = None 
        self.is_ready = threading.Event()

    def set_initial_state(self, estado: str):
     
        if self.estado_simulado is None: 
            print(f"  [SIMULADOR {self.nombre}] Estado inicial establecido a '{estado}' por el servidor.")
            self.estado_simulado = estado
            self.is_ready.set()

    def generate_next_values(self, t: int) -> dict | None:
        
        if not self.is_ready.is_set():
            return None 

        target_uso = 0
        if self.estado_simulado == 'Operativa':
            target_uso = self.config.get('Uso_operativo', 85)
        elif self.estado_simulado == 'Recuperación':
            target_uso = self.config.get('Uso_operativo', 85) * 0.6
        
        
        self.current_uso += (target_uso - self.current_uso) * 0.1 + random.uniform(-2, 2)
        self.current_uso = np.clip(self.current_uso, 0, 100)
        
        temp_base = self.config.get('Temp_min', 20)
        temp_max = self.config.get('Temp_max', 80)
        delta_uso = (self.current_uso / 100) * (temp_max - temp_base)
        delta_estado_temp = -5 if self.estado_simulado in ['Parada', 'Mantenimiento'] else 0
        self.current_temp += (temp_base + delta_uso + delta_estado_temp - self.current_temp) * 0.2 + random.uniform(-0.5, 0.5)
        self.current_temp = np.clip(self.current_temp, temp_base - 5, temp_max + 10)

        pres_base = self.config.get('Presion_base', 100)
        pres_max = self.config.get('Presion_maxima', 150)
        target_pres = pres_base + 0.4 * self.current_temp + 0.3 * self.current_uso
        delta_estado_pres = -20 if self.estado_simulado == 'Parada' else -25 if self.estado_simulado == 'Mantenimiento' else 0
        self.current_pres += (target_pres - self.current_pres) * 0.2 + delta_estado_pres + random.uniform(-3, 3)
        self.current_pres = np.clip(self.current_pres, pres_base - 10, pres_max + 15)

        return {
            "uso": self.current_uso,
            "temperatura": self.current_temp,
            "presion": self.current_pres
        }

def worker_linea(nombre_linea: str, config: dict):
 
    simulador = SensorSimulator(nombre_linea, config)
    ws_url = f"ws://{DJANGO_SERVER_IP}:8000/ws/maquinas/{quote(nombre_linea)}/"

    def on_message(ws, message: str):
    
        try:
            data = json.loads(message)
            if data.get('type') == 'initial_state_response':
                simulador.set_initial_state(data.get('estado_real_maquina'))
            else:
               
                print(f"<-- [{nombre_linea}] Recibido mensaje del servidor (ignorado): {data.get('type')}")
        except Exception as e:
            print(f"Error procesando mensaje para {nombre_linea}: {e}")

    def on_open(ws):
        print(f"### Conexión establecida para '{nombre_linea}'. Pidiendo estado inicial... ###")
        ws.send(json.dumps({"type": "request_initial_state"}))
        threading.Thread(target=run_simulation_loop, args=(ws, simulador), daemon=True).start()

    def run_simulation_loop(ws, sim: SensorSimulator):
        print(f"  [SIMULADOR {sim.nombre}] Hilo de envío esperando estado inicial...")
        sim.is_ready.wait(timeout=10)
        if not sim.is_ready.is_set():
            print(f"!!! [SIMULADOR {sim.nombre}] No se recibió estado inicial. El hilo no comenzará. !!!")
            ws.close()
            return

        print(f"  [SIMULADOR {sim.nombre}] Estado inicial '{sim.estado_simulado}' recibido. Iniciando envío de datos.")
        
        t = 0
        while True:
            try:
                sensor_data = sim.generate_next_values(t)
                if sensor_data:
                    message_to_send = {"type": "realtime_update", "payload": sensor_data}
                    ws.send(json.dumps(message_to_send))
                    print(f"-> [{sim.nombre}] Enviado (Simulando como '{sim.estado_simulado}'): Uso={sensor_data['uso']:.1f}%")
                t += 1
                time.sleep(random.uniform(5, 8))
            except Exception:
               
                break

    ws_app = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
    ws_app.run_forever()


def get_all_lineas_from_django(server_ip: str) -> list:
    api_url = f"http://{server_ip}:8000/qlearning/api/todas-las-lineas/"
    try:
        print(f"Obteniendo lista de todas las líneas desde {api_url}...")
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"!!! ERROR FATAL al obtener lista de líneas: {e}")
        return []

if __name__ == "__main__":
    print("--- Simulador de Sensores Multi-Línea (Modo Emisor Puro) ---")
    
    todas_las_lineas = get_all_lineas_from_django(DJANGO_SERVER_IP)
    
    if todas_las_lineas:
        threads = []
        for linea_info in todas_las_lineas:
            thread = threading.Thread(target=worker_linea, args=(linea_info['nombre'], linea_info['config']), daemon=True)
            threads.append(thread)
            thread.start()
            time.sleep(1)

        print(f"\n{len(threads)} simuladores iniciados en hilos separados. Presiona Ctrl+C para salir.")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nCerrando simulador...")
    else:
        print("\nNo se pudo iniciar. Verifique la conexión con el servidor Django.")