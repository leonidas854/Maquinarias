# q_learning/routing.py
from django.urls import re_path
from . import consumer

websocket_urlpatterns = [

    re_path(r'ws/maquina/(?P<nombre_linea>[^/]+)/$', consumer.MaquinaConsumer.as_asgi()),
]