# Entrenamiento.py
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.vec_env import DummyVecEnv
from Reportes.models import Lineas_Embotelladoras
from .Entorno_ import LineaAdaptativaEnv
from stable_baselines3.common.logger import configure


class Entrenamiento():
    def __init__(self):
        self.multi_env = None
        self.nombres_lineas = self._obtener_nombres_lineas()
        self.num_lineas = len(self.nombres_lineas)

    def _obtener_nombres_lineas(self):
        return list(Lineas_Embotelladoras.objects.values_list("Nombre", flat=True).order_by('id'))

    def _construir_entornos(self):
        def make_env(nombre, line_index, total_lines):
            def _init():
                return LineaAdaptativaEnv(nombre, line_index, total_lines)
            return _init

        envs = [make_env(nombre, i, self.num_lineas) 
                for i, nombre in enumerate(self.nombres_lineas)]
        
     
        self.multi_env = DummyVecEnv(envs)
        return self.multi_env
    
    def construir_entorno_evaluacion(self):
        nombres_lineas = list(Lineas_Embotelladoras.objects.values_list("Nombre", flat=True).order_by('id'))
        num_lineas = len(nombres_lineas)
        
        def make_env(nombre, idx, total_lines):
            def _init():
                return LineaAdaptativaEnv(nombre, idx, total_lines)
            return _init
            
        envs_eval = [make_env(nombre, i, num_lineas) for i, nombre in enumerate(nombres_lineas)]
        return DummyVecEnv(envs_eval)

    def entrenar_modelo(self):
      
        print("Construyendo entornos interactivos con normalización local...")
        self._construir_entornos()

        print(f"Entrenando un agente para {self.num_lineas} líneas.")
        print("Espacio de observación del entorno:", self.multi_env.observation_space)
        print("Ejemplo de shape de la observación:", self.multi_env.observation_space.sample().shape)
        print("Espacio de acción del entorno:", self.multi_env.action_space)

        model = PPO(
            "MlpPolicy",
            self.multi_env,
            verbose=1,
            learning_rate=0.0003,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            tensorboard_log="./ppo_tensorboard/"
        )
        log_dir = "./logs_entrenamiento/"
        new_logger = configure(log_dir, ["stdout", "csv", "tensorboard"])
        model.set_logger(new_logger)

        eval_env = self.construir_entorno_evaluacion()
        eval_callback = EvalCallback(
            eval_env,
            best_model_save_path="./mejor_modelo/",
            log_path="./logs_eval/",
            eval_freq=10000,
            deterministic=True,
            render=False
        )
       
        
        print("Iniciando entrenamiento del modelo PPO con evaluación periódica...")
        model.learn(total_timesteps=2_000_000, callback=eval_callback)

        print("Entrenamiento completado. Guardando modelo final...")
        model.save("modelo_multilinea_local_norm2")
        print("Modelo guardado.")