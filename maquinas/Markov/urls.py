from django.urls import path
from . import views

urlpatterns = [
    path('', views.Markov, name='markov'),
     path('prediccion/', views.predecir_markov, name='predecir_markov'),
     path('estado-actual/', views.obtener_estado_actual, name='estado_actual_markov'),
     path('prediccion/', views.predecir_markov, name='predecir_markov'),
     path('matriz-transiciones/', views.obtener_matriz_transiciones, name='obtener_matriz_transiciones'),



]