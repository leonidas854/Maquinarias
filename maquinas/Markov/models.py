from django.db import models
from django.contrib.auth.models import User
from Reportes.models import Lineas_Embotelladoras
from datetime import datetime

class Predice_estado(models.Model):
    Usuario_id = models.ForeignKey(User, on_delete=models.CASCADE)
    Linea_id = models.ForeignKey(Lineas_Embotelladoras, on_delete=models.CASCADE,related_name="Usuarios")
    Estado_actual = models.CharField(max_length=30,null=True, blank=True)
    Estado_calculado = models.CharField(max_length=30,null=True, blank=True)
    EstadoCalu = models.FloatField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    


