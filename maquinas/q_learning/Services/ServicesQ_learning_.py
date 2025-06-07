# ServicesQ_learning_.py
import numpy as np
import pandas as pd
from Reportes.models import Lineas_Embotelladoras
from Markov.Services.ServicesMarkov_ import ServicesMarkov
from typing import Dict, Any

class ServicesQ_learning():
    def __init__(self, name_linea: str):
            
            if not name_linea:
                raise ValueError("El nombre de la línea no puede ser nulo o vacío.")
            
            self.name_linea = name_linea
            self._actualizar_configuracion(name_linea)
            self.accion_a_estado_nombre = {
            0: 'Operativa',
            1: 'Parada',
            2: 'Mantenimiento',
            3: 'Recuperación',
            4: 'Reserva'
        }

        
    def set_linea(self, name_linea: str):
         self.name_linea = name_linea
         self._actualizar_configuracion(name_linea)
         
    def _actualizar_configuracion(self, name_linea: str):
        markov_service = ServicesMarkov(name_linea)
        self.linea_config = Lineas_Embotelladoras.objects.filter(Nombre=name_linea).values(
            'bph', 'Fecha_mantenimiento', 'Temp_min', 'Temp_max',
            'Uso_operativo', 'Criticidad', 'Presion_base', 'Presion_maxima'
        ).first() 
        if self.linea_config is None:
            raise ValueError(f"No se encontró la configuración para la línea: '{name_linea}' en la base de datos.")
        self.matriz = markov_service.get_matriz_probabilistica()
        self.estados = {i: estado for i, estado in enumerate(markov_service.get_estados())}
        self.estado_invertido = {v: k for k, v in self.estados.items()}
        
        ultimo_estado_info = markov_service.get_ultimo_estado()
        self.estado_actual = self.estado_invertido.get(ultimo_estado_info.get('estado'))
        
        self.estabilizador_euler = 10

    def tasa_por_criticidad(self, criticidad: str) -> float:
        return {'Alta': 0.6, 'Media': 0.3, 'Baja': 0.1}.get(criticidad, 0.2)

    def siguiente_estado(self, actual: int, matriz: np.ndarray) -> int:
  
        return np.random.choice(range(len(matriz)), p=matriz[actual])
    
    def uso_estado(self, estado_id: int) -> float:
   
        uso_op = self.linea_config['Uso_operativo'] / 100
        estado_nombre = self.estados.get(estado_id)
        valores = {'Operativa': uso_op, 'Parada': 0.0, 'Mantenimiento': 0.1, 'Recuperación': 0.6, 'Reserva': 0.2}
        return valores.get(estado_nombre, 0.0)

    def delta_presion_estado(self, estado_id: int) -> float:
     
        estado_nombre = self.estados.get(estado_id)
        valores = {'Operativa': 0.0, 'Parada': -20, 'Mantenimiento': -25, 'Recuperación': -10, 'Reserva': -15}
        return valores.get(estado_nombre, 0.0)
    
    def uso_logistico(self, t: float) -> float:
        criticidad = self.linea_config['Criticidad']
        max_uso = self.linea_config['Uso_operativo']
        tasa = self.tasa_por_criticidad(criticidad)
        return max_uso / (1 + np.exp(-tasa * (t - self.estabilizador_euler)))
    
    def fourier_temp(self, t: float, amplitud: float) -> float:
        return amplitud * np.sin((2 * np.pi * t) / 24) + 0.5 * np.sin((2 * np.pi * t) / 12)
    
    def simular_temperatura(self, t: float, uso: float, estado_id: int) -> float:
        T_base = self.linea_config['Temp_min']
        delta_uso = (uso / 100) * (self.linea_config['Temp_max'] - self.linea_config['Temp_min'])
        delta_estado = -5 if self.estados.get(estado_id) in ['Parada', 'Mantenimiento'] else 0
        deriva_desgaste = 0.001 * t 
        temperatura = T_base + self.fourier_temp(t, 4.0) + delta_uso + delta_estado + deriva_desgaste
        return np.clip(temperatura, 0, self.linea_config['Temp_max'] + 15) # Margen superior

    def simular_uso(self, t: float, estado_id: int) -> float:
        base = self.uso_logistico(t)
        factor_estado = self.uso_estado(estado_id)
        ruido = np.random.normal(0, 5)
        return np.clip(base * factor_estado + ruido, 0, 100)
    
    def simular_presion(self, temp: float, uso: float, estado_id: int) -> float:
        base_presion = self.linea_config["Presion_base"] + 0.4 * temp + 0.3 * uso + np.random.normal(0, 3.0)
        delta_estado = self.delta_presion_estado(estado_id)
        return np.clip(base_presion + delta_estado, 0, self.linea_config["Presion_maxima"] + 10) 
    
    def simular_siguiente_paso(self, t: int, estado_actual: Dict[str, Any], accion_agente: int) -> Dict[str, Any]:
        if accion_agente == 5: 
            estado_siguiente_id = self.siguiente_estado(estado_actual['id'], self.matriz)
        
        else:
            nombre_estado_deseado = self.accion_a_estado_nombre.get(accion_agente)
            if nombre_estado_deseado and nombre_estado_deseado in self.estado_invertido:
                estado_siguiente_id = self.estado_invertido[nombre_estado_deseado]
            else:
                
                estado_siguiente_id = self.siguiente_estado(estado_actual['id'], self.matriz)

      
        nuevo_uso = self.simular_uso(t, estado_siguiente_id)
        nueva_temp = self.simular_temperatura(t, nuevo_uso, estado_siguiente_id)
        nueva_presion = self.simular_presion(nueva_temp, nuevo_uso, estado_siguiente_id)

        if accion_agente == 2: 
            nueva_temp *= 0.90  
            nueva_presion *= 0.85 
        
        siguiente_estado_simulado = {
            'id': estado_siguiente_id,
            'nombre': self.estados[estado_siguiente_id],
            'uso': np.clip(nuevo_uso, 0, 100),
            'temperatura': np.clip(nueva_temp, 0, self.linea_config['Temp_max'] + 15),
            'presion': np.clip(nueva_presion, 0, self.linea_config['Presion_maxima'] + 10)
        }
        
        return siguiente_estado_simulado