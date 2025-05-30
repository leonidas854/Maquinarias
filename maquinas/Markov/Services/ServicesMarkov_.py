from q_learning.models import Simulacion_estado
from Reportes.models import Lineas_Embotelladoras
from .markov_ import Markov
import numpy as np
import pandas as pd
from Markov.models import Predice_estado
from django.contrib.auth.models import User
class ServicesMarkov:
    def __init__(self,Name_linea:str =None) :
        self.linea = Name_linea if Name_linea is not None else None
        
    def set_Name_linea(self,Name_linea:str):
        self.linea = Name_linea
    def get_ultimo_estado(self):
        try:
            linea = Lineas_Embotelladoras.objects.get(Nombre=self.linea)
            ultima = Simulacion_estado.objects.filter(
                Linea_id=linea,
                Invervencion=True
            ).order_by('-Fecha').first()
            if ultima:
                return {
                    'linea': linea.Nombre,
                    'fecha': ultima.Fecha,
                    'estado': ultima.acc_final
                }
            else:
                return {
                    'linea': linea.Nombre,
                    'mensaje': 'No se encontró un estado con intervención'
                }
        except Lineas_Embotelladoras.DoesNotExist:
            return {"error": "No se encontró la línea"}
        except Exception as e:
            return {"error": f"Error inesperado al obtener el último estado: {str(e)}"}

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
        try:
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

        except Exception as e:
            print("Error en construir_matriz_transicion:", str(e))
            return None

    def Resolver_probabilidad(self, saltos: int):
        try:
            markov = Markov()
            vector = self.get_vector_estados()
            matriz = self.construir_matriz_transicion()

            if vector is None:
                return {'error': 'No se pudo construir el vector: estado actual inválido'}

            if matriz is None or np.all(matriz == 0):
                return {'error': 'Matriz vacía: no hay transiciones suficientes'}
         
            markov.Convertir_Probabilidad(matriz)
            markov.set_vector(vector)

            resultado_vector = markov.Resolver_saltos(saltos)
            nombre_estados = self.get_estados()
            ultimo_estado = self.get_ultimo_estado()

            resultado = {
                'Estado_actual': ultimo_estado.get('estado'),
                'detalles': [
                    {'estado': nombre, 'probabilidad': prob}
                    for nombre, prob in zip(nombre_estados, resultado_vector)
                ]
            }
            return resultado

        except ValueError as ve:
            return {'error': f'Error de valor: {str(ve)}'}
        except Exception as e:
            return {'error': f'Error inesperado durante la predicción: {str(e)}'}

    def guardar_predicciones(self, usuario: User, saltos: int):
        try:
            resultado = self.Resolver_probabilidad(saltos)

            if 'error' in resultado:
                return resultado

            estado_actual = resultado['Estado_actual']
            detalles = resultado['detalles']

            linea = Lineas_Embotelladoras.objects.get(Nombre=self.linea)

            for detalle in detalles:
                nombre_estado = detalle['estado']
                prob = detalle['probabilidad']
                Predice_estado.objects.create(
                    Usuario_id=usuario,
                    Linea_id=linea,
                    Estado_actual=estado_actual,
                    Estado_calculado=nombre_estado,
                    EstadoCalu=round(prob, 4)
                )

            return {
                'mensaje': 'Todas las probabilidades fueron guardadas correctamente',
                'total_estados': len(detalles)
            }

        except Lineas_Embotelladoras.DoesNotExist:
            return {'error': 'No se encontró la línea para guardar predicciones'}
        except Exception as e:
            return {'error': f'Error al guardar predicciones: {str(e)}'}


        