from django.db import models
from django.contrib.auth.models import User
from Reportes.models import Lineas_Embotelladoras
class Simulacion_estado(models.Model):
    Linea_id = models.ForeignKey(Lineas_Embotelladoras, on_delete=models.CASCADE,related_name="Lineas_Simulacion")
    Usuario_id = models.ForeignKey(User, on_delete=models.CASCADE)
    Fecha = models.DateField()
    Acc_IA= models.CharField(max_length=40)
    Acc_humana = models.CharField(max_length=40)
    acc_final = models.CharField(max_length=40)
    Invervencion = models.BooleanField()
    Temperatura = models.FloatField()
    Presion = models.FloatField()
    Uso = models.FloatField()                   
    Recompensa = models.FloatField()
    Comentario= models.CharField(max_length=200)
    
