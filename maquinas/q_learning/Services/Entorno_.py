import gymnasium as gym
from gymnasium import spaces
import numpy as np
from .ServicesQ_learning_ import ServicesQ_learning


class LineaAdaptativaEnv(gym.Env):
    def __init__(self, nombre_linea, sensor_data, obs_space):
        super().__init__()
        self.sim = ServicesQ_learning(nombre_linea)
        self.config = self.sim.Linea_Config
        self.sensor_data = sensor_data
        self.current_step = 0

        self.observation_space = obs_space  
        self.action_space = spaces.Discrete(2)
        self.estado_map = self.sim.Estado_invertido  



    def reset(self, seed=None, options=None):
        self.current_step = 0
        if self.sensor_data.shape[1] != 4:
            raise ValueError("sensor_data debe tener columnas: [Uso, Temp, Presion, EstadoStr]")
        return self._get_obs(), {}
    
    


    def step(self, action):
        self.current_step += 1
        obs = self._get_obs()
        reward = self._get_reward(obs, action)
        done = self._is_done(obs)
        return obs, reward, done, False, {}

    def _get_obs(self):
        row = self.sensor_data[self.current_step]
        uso, temp, presion, estado_str = row
        if estado_str not in self.estado_map:
            raise ValueError(f"Estado desconocido: {estado_str}")
        estado_id = self.estado_map[estado_str]
        return np.array([uso, temp, presion, estado_id], dtype=np.float32)

    def _get_reward(self, obs, action):
        uso, temp, pres, estado_id = obs
        estado_nombre = self.sim.Estados.get(int(estado_id), "Operativa")

        if estado_nombre == "Mantenimiento" and action == 0:
            return -5  
        if estado_nombre == "Parada" and action == 1:
            return -3  
        if estado_nombre == "Recuperación" and uso > 50:
            return -2 
        if temp > self.config["Temp_max"] or pres > self.config["Presion_maxima"]:
            return -10
        elif action == 1:
            return -1
        return 1


    def _is_done(self, obs):
        _, temp, pres, _ = obs
        return (
            temp > self.config["Temp_max"] or 
            pres > self.config["Presion_maxima"] or 
            self.current_step >= len(self.sensor_data) - 1
        )
