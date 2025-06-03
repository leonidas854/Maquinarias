from django.db import models
from django.contrib.auth.models import User

class Lineas_Embotelladoras(models.Model):
    Nombre = models.CharField(max_length=30)
    Descripcion = models.CharField(max_length=200)
    bph = models.FloatField()
    Fecha_mantenimiento = models.CharField(max_length=50)
    Temp_min = models.FloatField()
    Temp_max = models.FloatField()
    Uso_operativo = models.FloatField()
    Criticidad = models.CharField(max_length=40)
    Presion_base = models.FloatField()
    Presion_maxima  = models.FloatField()
    botellas = models.ManyToManyField('Botella', related_name='lineas')
    usuarios = models.ManyToManyField(User, related_name="lineas_asignadas")
    def __str__(self):
        return self.Nombre
class Sabores(models.Model):
    Sabor = models.CharField(max_length=40)
    Abrev = models.CharField(max_length=40)
    def __str__(self):
        return self.Sabor


class Botella(models.Model):
    Nombre  = models.CharField(max_length=40)
    Envase  =  models.CharField(max_length=40)
    Abre_envase = models.CharField(max_length=40)
    Volumen = models.FloatField()
    sabores = models.ManyToManyField(Sabores, related_name='Botellas')
    def __str__(self):
        return self.Nombre


    

    
    
