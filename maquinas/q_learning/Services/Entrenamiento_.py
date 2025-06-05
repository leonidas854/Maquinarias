from  Markov.Services.ServicesMarkov_ import ServicesMarkov
from .ServicesQ_learning_ import ServicesQ_learning
import numpy as np 
from stable_baselines3.common.vec_env import DummyVecEnv

from .Entorno_ import LineaAdaptativaEnv
from stable_baselines3 import PPO
from Reportes.models import Lineas_Embotelladoras
from gymnasium import spaces
class Entrenamiento():
    def __init__(self,Name_linea:str =None) :
        self.Name_linea = Name_linea if Name_linea is not None else None
        
    def set_Linea(self,Name_linea:str):
         self.Name_linea = Name_linea
         
    def _calcular_espacio_global(self):
        nombres = self._obtener_nombres_lineas()
        temp_min = min(Lineas_Embotelladoras.objects.filter(Nombre=n).values_list("Temp_min", flat=True)[0] for n in nombres)
        temp_max = max(Lineas_Embotelladoras.objects.filter(Nombre=n).values_list("Temp_max", flat=True)[0] for n in nombres)
        pres_base = min(Lineas_Embotelladoras.objects.filter(Nombre=n).values_list("Presion_base", flat=True)[0] for n in nombres)
        pres_max = max(Lineas_Embotelladoras.objects.filter(Nombre=n).values_list("Presion_maxima", flat=True)[0] for n in nombres)
        
        return spaces.Box(
            low=np.array([0.0, temp_min, pres_base, 0]),
            high=np.array([100.0, temp_max, pres_max, 4]),
            dtype=np.float32
        )
         
         
    def _obtener_nombres_lineas(self):
        return list(Lineas_Embotelladoras.objects.values_list("Nombre", 
                                                              flat=True))  
    #solo sirve para entrenamiento esto 
    def _crear_env_por_linea(self,Name_linea:str =None,obs_space=None):
        q_learning = ServicesQ_learning(Name_linea)
        df = q_learning.Simulacion_Completa(365)
        sensor_data = df[['Uso', 'Temperatura', 'Presion', 'Estado']].values
       
        return lambda: LineaAdaptativaEnv(Name_linea,
                                          sensor_data,
                                          obs_space)


    def _Construir_Entornos(self):
        nombres_lineas = self._obtener_nombres_lineas()
        obs_space = self._calcular_espacio_global()

        def make_env(name):
            def _init():
                q_learning = ServicesQ_learning(name)
                df = q_learning.Simulacion_Completa(365)
                sensor_data = df[['Uso', 'Temperatura', 'Presion', 'Estado']].values
                return LineaAdaptativaEnv(name, sensor_data, obs_space)
            return _init

        envs = [make_env(nombre) for nombre in nombres_lineas]
        self.multi_env = DummyVecEnv(envs) 
        return self.multi_env



    
    def Entrenar_modelo(self):
        self._Construir_Entornos()
        model = PPO(
            "MlpPolicy",
            self.multi_env,
            verbose=1,
            learning_rate=0.0003,
            n_steps=512,
            batch_size=64
            )
        model.learn(total_timesteps=1_000_000)
        
        model.save("modelo_multilinea2")
    
    
    