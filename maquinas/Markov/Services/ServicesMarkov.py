from q_learning.models import Simulacion_estado

from Reportes.models import Lineas_Embotelladoras

class ServicesMarkov:
    def get_ultimo_estado(Name_linea:str):
        mi_linea = Lineas_Embotelladoras.objects.get(Nombre=Name_linea)
        ultima = Simulacion_estado.objects.filter(intervencion=True, linea_id= mi_linea.id).order_by('-fecha').first()
