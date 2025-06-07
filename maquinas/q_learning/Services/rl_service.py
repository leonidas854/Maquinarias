
from stable_baselines3 import PPO
import numpy as np
from q_learning.Services.ServicesQ_learning_ import ServicesQ_learning
from Reportes.models import Lineas_Embotelladoras

class RLModelManager:
    """
    Gestiona el modelo de RL como un Singleton para asegurar que se carga una sola vez.
    Proporciona métodos para hacer predicciones y simulaciones.
    """
    _model = None
    _lineas_info = None
    _accion_mapa = {
        0: 'Acción sugerida: Forzar a estado OPERATIVA.',
        1: 'Acción sugerida: Forzar a estado PARADA.',
        2: '¡ACCIÓN CRÍTICA! Realizar MANTENIMIENTO PREVENTIVO.',
        3: 'Acción sugerida: Forzar a estado RECUPERACIÓN.',
        4: 'Acción sugerida: Forzar a estado RESERVA.',
        5: 'Acción sugerida: SEGUIR OPERANDO (No intervenir).'
    }

    @classmethod
    def _initialize(cls):
        """Método privado para cargar el modelo y la información de las líneas."""
        if cls._model is None:
            print("Cargando modelo PPO en memoria...")
            # Asegúrate de que la ruta sea correcta desde la raíz del proyecto Django
            cls._model = PPO.load("modelo_multilinea_local_norm2.zip")
            print("Modelo cargado exitosamente.")

        if cls._lineas_info is None:
            print("Cargando configuración de líneas desde la BD...")
            lineas_db = list(Lineas_Embotelladoras.objects.values_list("Nombre", flat=True).order_by('id'))
            cls._lineas_info = {
                "nombres": lineas_db,
                "total": len(lineas_db),
                "indices": {nombre: i for i, nombre in enumerate(lineas_db)}
            }
            print("Configuración de líneas cargada.")

    @classmethod
    def get_model(cls):
        """Devuelve la instancia del modelo, inicializándola si es necesario."""
        cls._initialize()
        return cls._model

    @classmethod
    def get_line_info(cls, nombre_linea: str):
        """Devuelve el índice y el número total de líneas."""
        cls._initialize()
        if nombre_linea not in cls._lineas_info["indices"]:
            raise ValueError(f"La línea '{nombre_linea}' no se encontró en la configuración inicial.")
        return {
            "index": cls._lineas_info["indices"][nombre_linea],
            "total": cls._lineas_info["total"]
        }

    @classmethod
    def normalizar_observacion(cls, datos_reales: dict, nombre_linea: str, id_estado_actual: int):
        """Convierte datos de sensores en tiempo real al formato que el modelo espera."""
        line_info = cls.get_line_info(nombre_linea)
        sim_temp = ServicesQ_learning(nombre_linea) # Solo para obtener la config
        config = sim_temp.linea_config

        # Normalización de sensores
        uso_norm = datos_reales['uso'] / 100.0
        temp_range = config['Temp_max'] - config['Temp_min']
        temp_norm = (datos_reales['temperatura'] - config['Temp_min']) / temp_range if temp_range > 0 else 0
        pres_range = config['Presion_maxima'] - config['Presion_base']
        pres_norm = (datos_reales['presion'] - config['Presion_base']) / pres_range if pres_range > 0 else 0
        
        # One-hot encoding de la línea
        line_one_hot = np.zeros(line_info["total"], dtype=np.float32)
        line_one_hot[line_info["index"]] = 1.0

        # Construcción del vector de observación
        observacion = np.array([
            np.clip(uso_norm, 0, 1),
            np.clip(temp_norm, 0, 1),
            np.clip(pres_norm, 0, 1),
            float(id_estado_actual)
        ], dtype=np.float32)
        
        return np.concatenate([observacion, line_one_hot])

    @classmethod
    def traducir_accion(cls, id_accion: int) -> str:
        """Convierte el ID de la acción (0-5) a un texto legible."""
        return cls._accion_mapa.get(id_accion, "Acción desconocida")

# Opcional pero recomendado: Llama a _initialize() una vez cuando el módulo se importa.
# Esto hace que el modelo se cargue cuando Django inicia el servidor.
RLModelManager._initialize()