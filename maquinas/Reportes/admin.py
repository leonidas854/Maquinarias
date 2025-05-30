from django.contrib import admin

from .models import Lineas_Embotelladoras,Botella,Sabores



@admin.register(Botella)
class BotellaAdmin(admin.ModelAdmin):
    filter_horizontal = ('sabores',)

@admin.register(Sabores)
class SaboresAdmin(admin.ModelAdmin):
    list_display = ('Sabor', 'Abrev')

@admin.register(Lineas_Embotelladoras)
class LineasAdmin(admin.ModelAdmin):
    filter_horizontal = ('botellas',)