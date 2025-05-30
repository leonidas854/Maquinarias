from django.contrib import admin

from .models import Predice_estado

@admin.register(Predice_estado)
class Predice_estadoAdmin(admin.ModelAdmin):
    list_display = ('Usuario_id', 'Linea_id', 'Estado_actual', 'Estado_calculado', 'EstadoCalu', 'fecha')