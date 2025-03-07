# codeflow_backend/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import collaboration.routing  # Import the routing file

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codeflow_backend.settings")

# Get the HTTP application first
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            collaboration.routing.websocket_urlpatterns
        )
    ),
})