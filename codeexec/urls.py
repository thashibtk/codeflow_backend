
# codeexec/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CodeExecutionViewSet, execute_code_view

router = DefaultRouter()
router.register(r'executions', CodeExecutionViewSet, basename='code-execution')

urlpatterns = [
    path('', include(router.urls)),
    path('execute/', execute_code_view, name='execute-code'),
]