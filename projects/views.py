from rest_framework import viewsets, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Project, ProjectCollaborator, File
from .serializers import ProjectSerializer, ProjectCollaboratorSerializer, FileSerializer
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()

# 📂 Project ViewSet
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        project = serializer.save(creator=self.request.user)
        ProjectCollaborator.objects.create(project=project, user=self.request.user, permission="edit")

# 📂 Add Collaborator ViewSet
class AddCollaboratorView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, pk=None):
        project = get_object_or_404(Project, pk=pk)
        if project.creator != request.user:
            return Response({"error": "Only the creator can add collaborators"}, status=403)
        
        user_email = request.data.get("email")
        permission = request.data.get("permission", "view")

        user = get_object_or_404(User, email=user_email)
        ProjectCollaborator.objects.create(project=project, user=user, permission=permission)

        return Response({"message": "Collaborator added successfully"})

# 📂 File ViewSet (For Managing Files & Folders)
class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        project = get_object_or_404(Project, id=project_id)

        # Check if user is authorized
        if self.request.user != project.creator and not project.collaborators.filter(user=self.request.user).exists():
            return File.objects.none()

        return File.objects.filter(project=project)

    def perform_create(self, serializer):
        project_id = self.kwargs["project_id"]
        project = get_object_or_404(Project, id=project_id)

        # Check if user has 'edit' permissions
        if self.request.user != project.creator and not project.collaborators.filter(user=self.request.user, permission="edit").exists():
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        # Explicitly set the project before saving
        serializer.save(project=project)