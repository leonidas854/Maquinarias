from q_learning.models import Simulacion_estado
from Reportes.models import Lineas_Embotelladoras
from .Markov import Markov
import numpy as np
import pandas as pd
from Markov.models import Predice_estado
class ServicesMarkov:
    def __init__(self,Name_linea:str =None) :
        self.linea = Name_linea if Name_linea is not None else None
        
    def set_Name_linea(self,Name_linea:str):
        self.linea = Name_linea
    def get_ultimo_estado(self):
        try:
            linea = Lineas_Embotelladoras.objects.get(
                Nombre=self.linea)
            ultima = Simulacion_estado.objects.filter(
                Linea_id=linea,
                Intervencion = True
                 ).order_by('-Fecha').first()
            if ultima:
                return {
                    'linea':linea.Nombre,
                    'fecha':ultima.Fecha,
                    'estado':ultima.acc_final
                }
            else:
                return {
                    'linea':linea.Nombre,
                    'mensaje':'No se encontro un estado con intervencion'
                }
        except Lineas_Embotelladoras.DoesNotExist:
                return {
                    "error": "No se encontro la linea"
                }
    def get_estados (self):
       return list(
           Simulacion_estado.objects
           .values_list(
            'acc_final', flat=True)
           .distinct()
           .order_by('acc_final'))
    
    def get_vector_estados (self):
        Estados = self.get_estados()
        ultimo = self.get_ultimo_estado()
        estado_actual  = ultimo.get('estado') if 'estado' in ultimo else None
        if not estado_actual:
            return np.zeros(len(Estados))
        vector = [1 if estado ==estado_actual else 0 for estado in Estados]
        return np.array(vector)
        
    def construir_matriz_transicion(self):
        registros = Simulacion_estado.objects.filter(
            Linea_id__Nombre=self.linea
        ).values('Linea_id', 'Fecha', 'acc_final').order_by('Linea_id', 'Fecha')

        if not registros:
            return None

        df = pd.DataFrame.from_records(registros)
        df['siguiente_estado'] = df.groupby('Linea_id')['acc_final'].shift(-1)
        df = df.dropna(subset=['siguiente_estado'])

        transiciones = df.groupby(['acc_final', 'siguiente_estado']).size().unstack(fill_value=0)

        estados_ordenados = self.get_estados()
        transiciones = transiciones.reindex(index=estados_ordenados, columns=estados_ordenados, fill_value=0)
        return np.array(transiciones)
    def Resolver(self,saltos:int):
        markov = Markov()
        vector = self.get_vector_estados()
        matriz  = self.construir_matriz_transicion()
        if matriz is None or np.sum(vector)==0:
            return {'error':'No hay datos suficientes para calcular la cadena de Markov'}
        markov.Convertir_Probabilidad(matriz)
        markov.set_vector(vector)
        
        resultado_vector = markov.Resolver_saltos(saltos)
        nombre_estados = self.get_estados()
        ultimo_estado = self.get_ultimo_estado()
        resultado = {
            'Estado_actual':ultimo_estado.get('estado'),
            'detalles': 
                [{'estado':nombre,
            'probabilidad':prob}
            for nombre, prob in zip(nombre_estados,resultado_vector)]
        }
        return resultado
        
        
        
        