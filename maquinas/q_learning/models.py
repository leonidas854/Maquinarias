from django.db import models
from django.contrib.auth.models import User
from Reportes.models import Lineas_Embotelladoras
class Simulacion_estado(models.Model):
    Linea_id = models.ForeignKey(Lineas_Embotelladoras, on_delete=models.CASCADE,related_name="Lineas_Simulacion")
    Usuario_id = models.ForeignKey(User, on_delete=models.CASCADE)
    Fecha = models.DateField(null=True)
    Acc_IA= models.CharField(max_length=40,null=True, blank=True)
    Acc_humana = models.CharField(max_length=40,null=True, blank=True)
    acc_final = models.CharField(max_length=40,null=True, blank=True)
    Invervencion = models.BooleanField(null=True, blank=True)
    Temperatura = models.FloatField(null=True, blank=True)
    Presion = models.FloatField(null=True, blank=True)
    Uso = models.FloatField(null=True, blank=True)                   
    Recompensa = models.FloatField(null=True, blank=True)
    Comentario= models.CharField(max_length=200,null=True, blank=True)
    
