

import time  
import numpy as np
from stable_baselines3 import PPO
from Reportes.models import Lineas_Embotelladoras
from Markov.Services.ServicesMarkov_ import ServicesMarkov

class RLModelManager:
  
    _model = None
    _lineas_cache = {}  
    CACHE_TTL_SECONDS = 300  
    _accion_mapa = {
        0: 'Forzar a estado OPERATIVA.',
        1: 'Forzar a estado PARADA.',
        2: '¡ACCIÓN CRÍTICA! Realizar MANTENIMIENTO',
        3: 'Forzar a estado RECUPERACIÓN.',
        4: 'Forzar a estado RESERVA.',
        5: 'SEGUIR OPERANDO (No intervenir).'
    }

    @classmethod
    def _load_model(cls):
  
        if cls._model is None:
            print("--- [RLManager] Cargando modelo PPO en memoria por primera vez ---")
            cls._model = PPO.load("mejor_modelo/best_model.zip", device='cpu')
            print("--- [RLManager] Modelo PPO cargado exitosamente. ---")

    @classmethod
    def get_model(cls):
        cls._load_model()
        return cls._model

    @classmethod
    def _load_linea_config_from_db(cls, nombre_linea: str):
      
        print(f"--- [RLManager] CACHE MISS/EXPIRED. Cargando/Refrescando config para '{nombre_linea}' desde la BD... ---")
        
        linea_obj = Lineas_Embotelladoras.objects.filter(Nombre=nombre_linea).first()
        if not linea_obj:
            raise ValueError(f"No se encontró la línea '{nombre_linea}' en la base de datos.")

      
        markov_service = ServicesMarkov(nombre_linea)
        estados_lista = markov_service.get_estados()
        estados_map = {i: est for i, est in enumerate(estados_lista)}
        
     
        all_line_names = list(Lineas_Embotelladoras.objects.values_list("Nombre", flat=True).order_by('id'))
        if nombre_linea not in all_line_names:
            
            all_line_names.append(nombre_linea)
            all_line_names = sorted(list(set(all_line_names)))

    
        config_data = {
            "data": {
                "linea_config_dict": linea_obj.__dict__,
                "estados": estados_map,
                "estado_invertido": {v: k for k, v in estados_map.items()},
                "total_lineas": len(all_line_names),
                "index": all_line_names.index(nombre_linea)
            },
            "timestamp": time.time()  
        }
   
        cls._lineas_cache[nombre_linea] = config_data
        return config_data["data"]

    @classmethod
    def get_linea_config(cls, nombre_linea: str):
    
        cached_config = cls._lineas_cache.get(nombre_linea)
        
        if cached_config:
            age = time.time() - cached_config["timestamp"]
            if age < cls.CACHE_TTL_SECONDS:
              
                return cached_config["data"]
        
      
        return cls._load_linea_config_from_db(nombre_linea)

    @classmethod
    def normalizar_observacion(cls, datos_reales: dict, nombre_linea: str, nombre_estado_actual: str):
      
        cls._load_model()
        
    
        config_completa = cls.get_linea_config(nombre_linea)
        config_dict = config_completa['linea_config_dict']

       
        id_estado_actual = config_completa['estado_invertido'].get(nombre_estado_actual)
        if id_estado_actual is None:
            raise ValueError(f"El estado '{nombre_estado_actual}' no es válido o no está en el mapa de la línea '{nombre_linea}'.")

     
        uso_norm = datos_reales['uso'] / 100.0
        temp_range = config_dict['Temp_max'] - config_dict['Temp_min']
        temp_norm = (datos_reales['temperatura'] - config_dict['Temp_min']) / temp_range if temp_range > 0 else 0
        pres_range = config_dict['Presion_maxima'] - config_dict['Presion_base']
        pres_norm = (datos_reales['presion'] - config_dict['Presion_base']) / pres_range if pres_range > 0 else 0
        
      
        line_one_hot = np.zeros(config_completa["total_lineas"], dtype=np.float32)
        line_one_hot[config_completa["index"]] = 1.0

       
        observacion_sensores = np.array([
            np.clip(uso_norm, 0, 1),
            np.clip(temp_norm, 0, 1),
            np.clip(pres_norm, 0, 1),
            float(id_estado_actual)
        ], dtype=np.float32)
        
        return np.concatenate([observacion_sensores, line_one_hot])

    @classmethod
    def traducir_accion_descripcion(cls, id_accion: int) -> str:
        
        return cls._accion_mapa.get(id_accion, "Acción desconocida")
        
    @classmethod
    def traducir_accion(cls, id_accion: int) -> str:
     
        desc = cls.traducir_accion_descripcion(id_accion)
        if '¡ACCIÓN CRÍTICA! Realizar MANTENIMIENTO' in desc: return 'Mantenimiento'
        if 'Forzar a estado PARADA.' in desc: return 'Parada'
        if 'Forzar a estado OPERATIVA.' in desc: return 'Operativa'
        if 'Forzar a estado RECUPERACIÓN.' in desc: return 'Recuperación'
        if 'Forzar a estado RESERVA.' in desc: return 'Reserva'

