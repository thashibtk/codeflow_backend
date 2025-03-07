from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from meetings import serializers
from .models import Project, ProjectCollaborator, File
from .serializers import ProjectSerializer, ProjectCollaboratorSerializer, FileSerializer
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action

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


class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        if not project_id:
            return File.objects.none()
        return File.objects.filter(project_id=project_id)

    def perform_create(self, serializer):
        project_id = self.kwargs.get("project_id")
        parent_folder = self.request.data.get("parent_folder", None)
        name = self.request.data.get("name")

        # Check if a file/folder with the same name exists in the same parent folder
        if File.objects.filter(project_id=project_id, parent_folder=parent_folder, name=name).exists():
            raise serializers.ValidationError({"name": "A file or folder with this name already exists in this location."})

        serializer.save(project_id=project_id)

    def perform_update(self, serializer):
        instance = self.get_object()
        new_name = self.request.data.get("name", instance.name)
        parent_folder = instance.parent_folder

        # Check if renaming to an existing name
        if File.objects.filter(project=instance.project, parent_folder=parent_folder, name=new_name).exclude(id=instance.id).exists():
            raise serializers.ValidationError({"name": "A file or folder with this name already exists in this location."})

        serializer.save()

    def perform_destroy(self, instance):
        """ Recursively delete all child files/folders when deleting a folder """
        if instance.is_folder:
            self._delete_folder_contents(instance)
        instance.delete()

    def _delete_folder_contents(self, folder):
        children = File.objects.filter(parent_folder=folder)
        for child in children:
            if child.is_folder:
                self._delete_folder_contents(child)
            child.delete()

    @action(detail=True, methods=['get'], url_path='content', url_name='file-content')
    def content(self, request, project_id=None, pk=None):
        file_instance = get_object_or_404(File, id=pk, project_id=project_id)
        return Response({
            "id": file_instance.id,
            "name": file_instance.name,
            "content": file_instance.content,
            "project_id": file_instance.project.id,
            "is_folder": file_instance.is_folder
        })


# 📄 New File Content APIView
class FileContentView(APIView):
    """
    API view for handling file content operations.
    Supports both GET for retrieval and PUT for update.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, project_id, pk):
        """
        Retrieve file content
        """
        file_instance = get_object_or_404(File, id=pk, project_id=project_id)
        
        return Response({
            "id": file_instance.id,
            "name": file_instance.name,
            "content": file_instance.content,
            "project_id": file_instance.project.id,
            "is_folder": file_instance.is_folder
        })
    
    def put(self, request, project_id, pk):
        """
        Update file content
        """
        file_instance = get_object_or_404(File, id=pk, project_id=project_id)
        
        # Extract content from request
        content = request.data.get('content')
        if content is None:
            return Response(
                {"error": "Content field is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the file content
        file_instance.content = content
        file_instance.save()
        
        # Log successful update
        print(f"✅ Updated content for file '{file_instance.name}' (ID: {file_instance.id})")
        
        return Response({
            "id": file_instance.id,
            "name": file_instance.name,
            "message": "File content updated successfully"
        })