from django.contrib import admin
from .models import Lineas_Embotelladoras, Botella, Sabores
from django.contrib.auth.models import User


@admin.register(Sabores)
class SaborAdmin(admin.ModelAdmin):
    list_display = ('Sabor', 'Abrev')
    search_fields = ('Sabor', 'Abrev')


@admin.register(Botella)
class BotellaAdmin(admin.ModelAdmin):
    list_display = ('Nombre',  'Envase', 'Abre_envase','Volumen','mostrar_sabores')
    search_fields = ('Nombre', 'Envase')
    filter_horizontal = ('sabores',)

    def mostrar_sabores(self, obj):
        return ", ".join([s.Sabor for s in obj.sabores.all()])
    mostrar_sabores.short_description = 'Sabores'


@admin.register(Lineas_Embotelladoras)
class LineasAdmin(admin.ModelAdmin):
    list_display = (
        'Nombre', 'Descripcion', 'bph', 'Fecha_mantenimiento',
        'Temp_min', 'Temp_max', 'Uso_operativo', 'Criticidad',
        'mostrar_botellas', 'mostrar_usuarios'
    )
    search_fields = ('Nombre', 'Descripcion', 'Criticidad')
    filter_horizontal = ('botellas', 'usuarios')
    list_filter = ('Criticidad',)

    def mostrar_botellas(self, obj):
        return ", ".join([b.Nombre for b in obj.botellas.all()])
    mostrar_botellas.short_description = 'Botellas'

    def mostrar_usuarios(self, obj):
        return ", ".join([u.username for u in obj.usuarios.all()])
    mostrar_usuarios.short_description = 'Usuarios Asignados'
