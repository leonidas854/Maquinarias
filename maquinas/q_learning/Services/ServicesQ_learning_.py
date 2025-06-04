import sys
import os
from  Markov.Services.ServicesMarkov_ import ServicesMarkov
import pandas as pd
from Reportes.models import Lineas_Embotelladoras
import numpy as np
class ServicesQ_learning():
    def __init__(self,Name_linea:str =None) :
        self.Name_linea = Name_linea
        self._actualizar_configuracion(Name_linea)
        
    def set_Linea(self,Name_linea:str):
         self.Name_linea = Name_linea
         self._actualizar_configuracion(Name_linea)
         
    def _actualizar_configuracion(self, Name_linea):
        markov_service = ServicesMarkov(Name_linea)
        self.Matriz = markov_service.get_matriz_probabilistica()
        self.Estados = {i: estado for i, estado in enumerate(markov_service.get_estados())}
        self.Linea_Config = Lineas_Embotelladoras.objects.filter(Nombre=Name_linea).values(
            'bph', 'Fecha_mantenimiento', 'Temp_min', 'Temp_max',
            'Uso_operativo', 'Criticidad','Presion_base', 'Presion_maxima'
        ).first()
        Estado_invertido = {v: k for k, v in self.Estados.items()}
        ultimo_estado_info = markov_service.get_ultimo_estado()
        if 'estado' in ultimo_estado_info:
            self.estado_actual = Estado_invertido.get(ultimo_estado_info['estado']) 

        self.Estabilizador_euler = 10

    def tasa_por_criticidad(self,Criticidad):
        return {
        'Alta': 0.6,
        'Media': 0.3,
        'Baja': 0.1
        }.get(Criticidad,0.2)
   

    def Siguiente_estado(self,actual,matriz):
        return np.random.choice(range(len(matriz)),p=matriz[actual])
    
    def uso_estado(self, estado_id):

        uso_op = self.Linea_Config['Uso_operativo']/100
        estado_nombre = self.Estados.get(estado_id)
        valores_por_estado = {
        'Operativa': uso_op ,  
        'Parada': 0.0,
        'Mantenimiento': 0.1,
        'Recuperación': 0.6,
        'Reserva': 0.2
        }
        return valores_por_estado.get(estado_nombre)  


    def delta_presion_estado(self, estado_id):
        estado_nombre = self.Estados.get(estado_id)
        valores_por_estado = {
            'Operativa': 0.0,
            'Parada': -20,
            'Mantenimiento': -25,
            'Recuperación': -10,
            'Reserva': -15
        }
        return valores_por_estado.get(estado_nombre)

        
        
    def uso_logistico(self,t):
        criticidad = self.Linea_Config['Criticidad']
        max_uso = self.Linea_Config['Uso_operativo']
        tasa = self.tasa_por_criticidad(criticidad)
        return max_uso/( 1 + np.exp(-tasa * (t - self.Estabilizador_euler) ))
    
    def fourier_temp(self,t,amplitud):
        return amplitud * np.sin((2 * np.pi * t)/24) + 0.5*np.sin((2 * np.pi * t)/12)
    
    def euler_temp(self,t,k):
        return (1-np.exp( -k * t )) * self.Estabilizador_euler
    
    def uso_temp(self,uso):
        return (uso/100)*(self.Linea_Config['Temp_max'] - self.Linea_Config['Temp_min'])
    
    def Simular_temperatura(self,t,uso,estado):
        T_base = self.Linea_Config['Temp_min']
        fourier = self.fourier_temp(t,2.0)
        delta_uso = self.uso_temp(uso)
        delta_estado = -5 if estado in [1,2] else 0
        temperatura = T_base + fourier + delta_uso + delta_estado
        return np.clip(temperatura, 0, self.Linea_Config['Temp_max'])
    
    def simular_uso(self,t,estado):
        base  = self.uso_logistico(t)
        factor_estado = self.uso_estado(estado)
        ruido = np.random.normal(0,2)
        return np.clip(base*factor_estado + ruido, 0, 100)
    
    def simular_presion(self,temp, uso, estado):
        base_presion = self.Linea_Config["Presion_base"]+ 0.3 * temp + 0.2 * uso + np.random.normal(0, 1.5)
        delta_estado = self.delta_presion_estado(estado)
        return np.clip(base_presion + delta_estado, 0, self.Linea_Config["Presion_maxima"])
    
    def Simulacion_Completa(self,t):
        #los datos entran por dias
        t = t *24
        t_range =  np.arange(0, t, 1)
        estado =  self.estado_actual
        estados,usos,temperaturas,presiones = [],[],[],[]
        for t in t_range:
            uso = self.simular_uso(t, estado)
            temp = self.Simular_temperatura(t,uso,estado)
            pres = self.simular_presion(temp, uso, estado)
            estados.append(self.Estados[estado])
            usos.append(uso)
            temperaturas.append(temp)
            presiones.append(pres)
            estado = self.Siguiente_estado(estado, self.Matriz)
        df_sim = pd.DataFrame({'Hora':t_range,
                               'Estado':estados,
                               'Uso':usos,
                               'Temperatura':temperaturas,
                               'Presion':presiones})
        return df_sim
        
        