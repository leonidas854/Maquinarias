from django.urls import path
from . import views
from . import consumer
app_name = 'q_learning'
urlpatterns = [
    
    path('', views.select_linea_dashboard, name='select_linea_dashboard'),
    
    path('dashboard/<str:nombre_linea>/', views.qlearning_dashboard, name='qlearning_dashboard'),
    
    path('api/estado-actual/', views.get_linea_estado_actual, name='api_get_estado_actual'),
    
    path('api/configuracion/', views.get_linea_config, name='api_get_linea_config'),
    
    path('api/todas-las-lineas/', views.get_todas_las_lineas, name='api_get_todas_las_lineas'),
    
    path('api/ajuste-manual/', views.registrar_ajuste_manual, name='api_ajuste_manual'),
    path('manual/', views.ajuste_manual_view, name='ajuste_manual_view'),
]