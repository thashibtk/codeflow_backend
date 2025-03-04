from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, AddCollaboratorView, FileViewSet

# Main Router for Projects
router = DefaultRouter()
router.register(r'', ProjectViewSet)

# Router for handling files inside a project
file_router = DefaultRouter()
file_router.register(r'files', FileViewSet, basename='files')

urlpatterns = [
    path('', include(router.urls)),  # Project Endpoints
    path('<uuid:pk>/add-collaborator/', AddCollaboratorView.as_view({'post': 'create'})),  # Add Collaborator

    path('<uuid:project_id>/files/', FileViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<uuid:project_id>/files/<uuid:pk>/', FileViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

]
