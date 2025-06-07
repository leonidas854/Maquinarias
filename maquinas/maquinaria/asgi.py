"""
ASGI config for maquinaria project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack




os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maquinaria.settings')

django.setup()

import q_learning.routing
http_application = get_asgi_application()


application = ProtocolTypeRouter({
    "http": http_application,
    "websocket": AuthMiddlewareStack(
        URLRouter(
             q_learning.routing.websocket_urlpatterns
        )
    ),
})