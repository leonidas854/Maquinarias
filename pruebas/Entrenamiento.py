from stable_baselines3 import PPO
import numpy as np
from EquipoEnt import EquipoEnt


# Datos de ejemplo: [temperatura, vibración, presión]
sensor_data = np.array([
    [30, 2, 100],   # Paso 1: Estado normal
    [35, 3, 110],   # Paso 2
    [40, 4, 120],   # Paso 3
    [50, 5, 130],   # Paso 4
    [60, 6, 140],   # Paso 5: Vibración aumenta
    [70, 7, 150],   # Paso 6: Señal de advertencia
    [85, 9, 200],   # Paso 7: ¡Fallo inminente! (temp > 80, vibración > 8)
    [90, 10, 250],  # Paso 8: Máquina fallando
], dtype=np.float32)
# Crear el entorno con datos de sensores (simulados o reales)
env = EquipoEnt(sensor_data)

# Inicializar el modelo PPO
model = PPO(
    "MlpPolicy",       # Usar una red neuronal MLP (para estados continuos)
    env,               # Entorno personalizado
    verbose=1,         # Mostrar logs durante el entrenamiento
    learning_rate=0.001,  # Tasa de aprendizaje (opcional)
    n_steps=2048,      # Pasos por iteración (opcional)
)

# Entrenar el modelo
model.learn(total_timesteps=10000)  # 10,000 interacciones con el entorno

# Guardar el modelo entrenado
model.save("modelo_predictivo")
