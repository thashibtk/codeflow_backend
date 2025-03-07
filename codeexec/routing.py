# codeexec/.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/codeexec/project/(?P<project_id>[^/]+)/$', consumers.CodeExecutionConsumer.as_asgi()),
]