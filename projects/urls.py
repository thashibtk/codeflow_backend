from django.urls import path
from .views import ProjectViewSet, AddCollaboratorView, FileViewSet, FileContentView

urlpatterns = [
    # Project endpoints
    path('', ProjectViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<uuid:pk>/', ProjectViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    # Add Collaborator
    path('<uuid:pk>/add-collaborator/', AddCollaboratorView.as_view({'post': 'create'})),

    # File Management
    path('<uuid:project_id>/files/', FileViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<uuid:project_id>/files/<int:pk>/', FileViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    # File Content handling with dedicated APIView
    path('<uuid:project_id>/files/<int:pk>/content/', FileContentView.as_view()),
]