import gymnasium
from gymnasium import spaces
import numpy as np

class Entorno(gymnasium.Env):
    def __init__(self):
        super(Entorno, self).__init__()
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32)