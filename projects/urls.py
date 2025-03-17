from django.urls import path
from .views import ProjectViewSet, CollaboratorViewSet, FileViewSet, FileContentView

urlpatterns = [
    # Project endpoints
    path('', ProjectViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<uuid:pk>/', ProjectViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    # Collaborator endpoints
    path('<uuid:project_id>/collaborators/', 
         CollaboratorViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='project-collaborators'),
    path('<uuid:project_id>/collaborators/<int:collaborator_id>/', 
         CollaboratorViewSet.as_view({'delete': 'destroy', 'put': 'update', 'patch': 'update'}),
         name='collaborator-detail'),

    # File Management
    path('<uuid:project_id>/files/', 
         FileViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='project-files'),
    path('<uuid:project_id>/files/<int:pk>/', 
         FileViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}),
         name='file-detail'),

    # File Content handling with dedicated APIView
    path('<uuid:project_id>/files/<int:file_id>/content/', 
         FileContentView.as_view(),
         name='file-content'),
]