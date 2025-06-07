from django.urls import path
from . import views
from . import consumer

urlpatterns = [
    
    path('', views.select_linea_dashboard, name='select_linea_dashboard'),
    
    path('dashboard/<str:nombre_linea>/', views.qlearning_dashboard, name='qlearning_dashboard'),
    
    path('api/estado-actual/', views.get_linea_estado_actual, name='api_get_estado_actual'),
    
    path('api/configuracion/', views.get_linea_config, name='api_get_linea_config'),
    
]