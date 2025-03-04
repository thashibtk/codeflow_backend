from django.urls import path
from .views import CodeExecutionView

urlpatterns = [
    path("execute/", CodeExecutionView.as_view(), name="execute_code"),
]
