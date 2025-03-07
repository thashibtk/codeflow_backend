# collaboration/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/collaborators/(?P<project_id>[\w-]+)/$', consumers.CollaboratorConsumer.as_asgi()),
]