from django.db import models

class Lineas_Embotelladoras(models.Model):
    Nombre = models.CharField(max_length=30)
    Descripcion = models.CharField(max_length=200)
    bph = models.FloatField()
    Fecha_mantenimiento = models.DateField()
    Temp_min = models.FloatField()
    Temp_max = models.FloatField()
    Uso_operativo = models.FloatField()
    Criticidad = models.CharField(max_length=40)


class Botella(models.Model):
    Linea_id= models.ForeignKey('Lineas_Embotelladoras', on_delete=models.CASCADE,related_name="Botellas")
    Nombre  = models.CharField(max_length=40)
    Cantidad  = models.IntegerField()
    Volumen  =  models.FloatField()
    Envase  =  models.CharField(max_length=40)
    
class Sabores(models.Model):
    Botella_id = models.ForeignKey('Botella', on_delete=models.CASCADE,related_name="Botellas")
    Sabor = models.CharField(max_length=40)
    Abrev = models.CharField(max_length=40)
    
    
