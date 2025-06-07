# Entorno_.py
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from .ServicesQ_learning_ import ServicesQ_learning 

class LineaAdaptativaEnv(gym.Env):
    metadata = {'render_modes': []}

    def __init__(self, nombre_linea: str, line_index: int, total_lines: int):
        super().__init__()
        self.nombre_linea = nombre_linea
        self.sim = ServicesQ_learning(nombre_linea)
        
        self.config = self.sim.linea_config
        
        self.line_index = line_index
        self.total_lines = total_lines
        self.line_one_hot = np.zeros(self.total_lines, dtype=np.float32)
        if self.total_lines > 0:
            self.line_one_hot[self.line_index] = 1.0

        low_obs = np.concatenate(([0.0, 0.0, 0.0, 0.0], np.zeros(self.total_lines)))

        high_obs = np.concatenate(([1.0, 1.0, 1.0,
                                    len(self.sim.estados) - 1.0],
                                   np.ones(self.total_lines)))

        self.observation_space = spaces.Box(
            low=low_obs.astype(np.float32),
            high=high_obs.astype(np.float32),
            dtype=np.float32
        )
        
        self.action_space = spaces.Discrete(6)
        self.current_step = 0
        self.estado_actual = None

    def _normalizar_obs(self, obs_dict):
        uso_norm = obs_dict['uso'] / 100.0
        
        temp_range = self.config['Temp_max'] - self.config['Temp_min']
        temp_norm = (obs_dict['temperatura'] - self.config['Temp_min']) / temp_range if temp_range > 0 else 0
        
        pres_range = self.config['Presion_maxima'] - self.config['Presion_base']
        pres_norm = (obs_dict['presion'] - self.config['Presion_base']) / pres_range if pres_range > 0 else 0
        
        datos_sensores = np.array([
            np.clip(uso_norm, 0, 1),
            np.clip(temp_norm, 0, 1),
            np.clip(pres_norm, 0, 1),
            float(obs_dict['id']) 
        ], dtype=np.float32)
        
        return np.concatenate([datos_sensores, self.line_one_hot])

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        initial_state_id = np.random.choice(list(self.sim.estados.keys()))
        self.estado_actual = {
            'id': initial_state_id, 'nombre': self.sim.estados[initial_state_id],
            'uso': self.sim.simular_uso(0, initial_state_id),
            'temperatura': self.sim.simular_temperatura(0, 50, initial_state_id),
            'presion': self.sim.simular_presion(self.config['Temp_min'], 50, initial_state_id)
        }
        self.estado_anterior = self.estado_actual.copy()
        obs = self._normalizar_obs(self.estado_actual)
        return obs, {}

    def step(self, action):
        self.current_step += 1
        self.estado_anterior = self.estado_actual.copy() 
        estado_siguiente_simulado = self.sim.simular_siguiente_paso(
            t=self.current_step,
            estado_actual=self.estado_actual,
            accion_agente=action
        )
        
        self.estado_actual = estado_siguiente_simulado
        
        
        reward = self._get_reward(action)
        obs = self._normalizar_obs(self.estado_actual)

        terminated = self._is_catastrofico()
        truncated = self.current_step >= (365 * 24)
        
        
        return obs, reward, terminated, truncated, {}

    def _get_reward(self, action: int) -> float:
        reward = 0.0
        estado_nombre = self.estado_actual['nombre']
        temp = self.estado_actual['temperatura']
        pres = self.estado_actual['presion']
        
       
        if estado_nombre == 'Operativa':
            reward += 5.0

        elif estado_nombre in ['Parada', 'Mantenimiento']:
            reward -= 5.0

        elif estado_nombre in ['Recuperación', 'Reserva']:
            reward -= 1.0

    
        temp_max = self.config["Temp_max"]
        pres_max = self.config["Presion_maxima"]
        if temp > temp_max * 0.8:
            reward -= 2.0 * ((temp - temp_max * 0.8) / (temp_max * 0.2)) 
        if pres > pres_max * 0.8:
            reward -= 2.0 * ((pres - pres_max * 0.8) / (pres_max * 0.2)) 
            
 
        if temp > temp_max: reward -= 20.0
        if pres > pres_max: reward -= 20.0

      
        estado_anterior_nombre = self.estado_anterior['nombre']
        
     
        if action != 5: 
             reward -= 0.5 
        
     
        if self.sim.accion_a_estado_nombre.get(action) == estado_anterior_nombre:
            reward -= 10.0 

     
        is_healthy = (self.estado_anterior['temperatura'] < temp_max * 0.8 and
                      self.estado_anterior['presion'] < pres_max * 0.8)
        if estado_anterior_nombre == 'Operativa' and is_healthy and action in [1, 2, 4]: 
            reward -= 15.0 
            
        is_at_risk = (self.estado_anterior['temperatura'] > temp_max * 0.8 or
                      self.estado_anterior['presion'] > pres_max * 0.8)
        if is_at_risk and action == 2: # Mantenimiento
            reward += 20.0 
    
        if estado_anterior_nombre in ['Mantenimiento', 'Parada', 'Recuperación'] and action == 0:
            reward += 10.0
            
        return reward

    def _is_catastrofico(self) -> bool:
    
        temp_catastrofica = self.config["Temp_max"] * 1.1 
        pres_catastrofica = self.config["Presion_maxima"] * 1.1
        return (self.estado_actual['temperatura'] > temp_catastrofica or 
                self.estado_actual['presion'] > pres_catastrofica)

    def _is_done(self):
       
        max_steps = 365 * 24
        return self._is_catastrofico() or self.current_step >= max_steps