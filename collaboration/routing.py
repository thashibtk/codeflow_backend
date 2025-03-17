from django.urls import re_path
from collaboration.consumers import CollaboratorConsumer

websocket_urlpatterns = [
    re_path(r"ws/collaborators/(?P<project_id>[\w-]+)/$", CollaboratorConsumer.as_asgi()),
]