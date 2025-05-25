from stable_baselines3 import PPO
import numpy as np

from EquipoEnt import EquipoEnt

# Cargar el modelo
model = PPO.load("modelo_predictivo")  # Asegúrate de que la ruta sea correcta

# Datos de sensores nuevos (simulados o reales)
new_sensor_data = np.array([
    [30, 2, 100],  # Estado normal
    [65, 7, 150],  # Señal de advertencia
    [82, 8, 200],  # ¡Fallo inminente!
], dtype=np.float32)

# Crear el entorno con los nuevos datos
env = EquipoEnt(new_sensor_data)

# Reiniciar el entorno y obtener el estado inicial
obs, _ = env.reset()  # Devuelve (obs, info)

for _ in range(len(new_sensor_data)):
    # Predecir la acción óptima con el modelo
    action, _ = model.predict(obs, deterministic=True)  # deterministic=True para evitar aleatoriedad

    # Ejecutar la acción en el entorno
    obs, reward, terminated, truncated, info = env.step(action)

    # Mostrar resultados
    print(f"Estado actual: {obs}")
    print(f"Acción tomada: {'Mantenimiento' if action == 1 else 'Continuar operando'}")
    print(f"Recompensa: {reward}")

    if terminated or truncated:
        print("¡Alerta: La máquina requiere intervención!")
        break