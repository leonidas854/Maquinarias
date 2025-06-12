from django.urls import path
from . import views

urlpatterns = [  
               
path('', views.reportes_view, name='reportes'),
 path('api/reporte-qlearning/', views.reporte_qlearning_data, name='api_reporte_qlearning'),
 path('api/reporte-entrenamiento/', views.reporte_entrenamiento_data, name='api_reporte_entrenamiento'),
 
 
 
 
]
               
               
               
               
