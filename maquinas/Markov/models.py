from django.db import models
from django.contrib.auth.models import User
from Reportes.models import Lineas_Embotelladoras

class Predice_estado(models.Model):
    Usuario_id = models.ForeignKey(User, on_delete=models.CASCADE)
    Linea_id = models.ForeignKey(Lineas_Embotelladoras, on_delete=models.CASCADE,related_name="Usuarios")
    Estado_esperado = models.CharField(max_length=30)
    Estado_calculado = models.CharField(max_length=30)
    EstadoCalu = models.IntegerField()
    


