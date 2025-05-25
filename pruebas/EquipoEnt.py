import gymnasium
from gymnasium import spaces
import numpy as np


class EquipoEnt(gymnasium.Env):

    def __init__(self, sensor_data):
        super(EquipoEnt, self).__init__()
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0]),
            high=np.array([100, 10, 500]),
            dtype=np.float32
        )
        self.action_space = spaces.Discrete(2)
        self.sensor_data = sensor_data
        self.current_step = 0

    def reset(self, seed=None, options=None):
        self.current_step = 0
        initial_state = self.sensor_data[self.current_step]
        return initial_state, {}  # Devuelve (obs, info)

    def step(self, action):
        self.current_step += 1
        next_state = self.sensor_data[self.current_step]
        reward = self._calculate_reward(next_state, action)
        terminated = self._is_done(next_state)  # True si la máquina falla
        truncated = False  # Siempre False (a menos que haya un límite de tiempo)
        info = {}
        return next_state, reward, terminated, truncated, info  # ¡Ahora 5 valores!

    def _calculate_reward(self, state, action):
        # Lógica de recompensa (ej: penalizar fallos, recompensar buen estado)
        temperature, vibration, pressure = state

        if temperature > 80 or vibration > 8:  # Condición de fallo
            return -10
        elif action == 1:  # Si el agente decide hacer mantenimiento
            return -1  # Costo de mantenimiento
        else:
            return 1  # Recompensa por operación normal

    def _is_done(self, state):
        # Terminar episodio si la máquina falla o se acaban los datos
        temperature, vibration, pressure = state
        return temperature > 80 or vibration > 8 or self.current_step >= len(self.sensor_data) - 1