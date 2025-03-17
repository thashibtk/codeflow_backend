from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Project, ProjectCollaborator, File
from .serializers import ProjectSerializer, ProjectCollaboratorSerializer, FileSerializer
from django.contrib.auth import get_user_model
from rest_framework import status
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers  # ✅ Add this import


User = get_user_model()

# 📂 Project ViewSet
class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(
            Q(creator=user) | Q(collaborators__user=user)
        ).distinct()

    def perform_create(self, serializer):
        project = serializer.save(creator=self.request.user)
        ProjectCollaborator.objects.create(project=project, user=self.request.user, permission="edit")

    def update(self, request, *args, **kwargs):
        project = self.get_object()
        user = request.user

        if project.creator == user:
            return super().update(request, *args, **kwargs)

        collaborator = ProjectCollaborator.objects.filter(project=project, user=user).first()
        if not collaborator or collaborator.permission != "edit":
            return Response({"error": "You do not have permission to edit this project"}, status=status.HTTP_403_FORBIDDEN)

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()

        if project.creator != request.user:
            return Response({"error": "Only the project creator can delete this project"}, status=status.HTTP_403_FORBIDDEN)

        return super().destroy(request, *args, **kwargs)
        

class CollaboratorViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request, project_id=None):
        """ Retrieve all collaborators of a project """
        project = get_object_or_404(Project, id=project_id)

        if project.creator != request.user and not ProjectCollaborator.objects.filter(project=project, user=request.user).exists():
            return Response({"error": "You do not have permission to view collaborators"}, status=status.HTTP_403_FORBIDDEN)

        collaborators = ProjectCollaborator.objects.filter(project=project)
        serializer = ProjectCollaboratorSerializer(collaborators, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def create(self, request, project_id=None):  
        project = get_object_or_404(Project, id=project_id)

        if project.creator != request.user:
            return Response({"error": "Only the creator can add collaborators"}, status=status.HTTP_403_FORBIDDEN)

        user_email = request.data.get("email")
        permission = request.data.get("permission", "view")

        if not user_email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, email=user_email)

        if ProjectCollaborator.objects.filter(project=project, user=user).exists():
            return Response({"error": "User is already a collaborator"}, status=status.HTTP_400_BAD_REQUEST)

        collaborator = ProjectCollaborator.objects.create(project=project, user=user, permission=permission)
        serializer = ProjectCollaboratorSerializer(collaborator)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, project_id=None, collaborator_id=None):
        project = get_object_or_404(Project, id=project_id)

        if project.creator != request.user:
            return Response({"error": "Only the creator can change collaborator permissions"}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        collaborator = get_object_or_404(ProjectCollaborator, id=collaborator_id, project=project)
        
        # Get the new permission from request data
        permission = request.data.get("permission")
        if not permission or permission not in ["view", "edit"]:
            return Response({"error": "Valid permission (view/edit) is required"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        collaborator.permission = permission
        collaborator.save()
        
        serializer = ProjectCollaboratorSerializer(collaborator)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, project_id=None, collaborator_id=None):
        """ Remove a collaborator from a project """
        project = get_object_or_404(Project, id=project_id)

        if project.creator != request.user:
            return Response({"error": "Only the creator can remove collaborators"}, status=status.HTTP_403_FORBIDDEN)
        
        collaborator = get_object_or_404(ProjectCollaborator, id=collaborator_id, project=project)
        collaborator.delete()
        
        return Response({"message": "Collaborator removed successfully"}, status=status.HTTP_204_NO_CONTENT)


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
        project = get_object_or_404(Project, id=project_id)
        user = self.request.user

        # Check if user has 'edit' permission
        collaborator = ProjectCollaborator.objects.filter(project=project, user=user).first()
        if not collaborator or collaborator.permission != "edit":
            raise serializers.ValidationError({"error": "You do not have permission to add files."})

        try:
            serializer.save(project=project)
        except Exception as e:
            print("❌ Error while creating file:", str(e))  # Logs the actual error
            raise serializers.ValidationError({"error": str(e)})


    def perform_update(self, serializer):
        instance = self.get_object()
        user = self.request.user

        # Check if user has 'edit' permission
        collaborator = ProjectCollaborator.objects.filter(project=instance.project, user=user).first()
        if not collaborator or collaborator.permission != "edit":
            raise serializers.ValidationError({"error": "You do not have permission to edit this file."})

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user

        # Check if user has 'edit' permission
        collaborator = ProjectCollaborator.objects.filter(project=instance.project, user=user).first()
        if not collaborator or collaborator.permission != "edit":
            raise serializers.ValidationError({"error": "You do not have permission to delete this file."})

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


class FileContentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, project_id, file_id):
        file_instance = get_object_or_404(File, id=file_id, project_id=project_id)
        return Response({
            "id": file_instance.id,
            "name": file_instance.name,
            "content": file_instance.content,
            "project_id": file_instance.project.id,
            "is_folder": file_instance.is_folder
        })
    
    def put(self, request, project_id, file_id):
        file_instance = get_object_or_404(File, id=file_id, project_id=project_id)
        user = request.user

        # Check if user has 'edit' permission
        collaborator = ProjectCollaborator.objects.filter(project=file_instance.project, user=user).first()
        if not collaborator or collaborator.permission != "edit":
            return Response({"error": "You do not have permission to edit this file."}, status=status.HTTP_403_FORBIDDEN)

        content = request.data.get('content')
        if content is None:
            return Response({"error": "Content field is required"}, status=status.HTTP_400_BAD_REQUEST)

        file_instance.content = content
        file_instance.save()

        return Response({
            "id": file_instance.id,
            "name": file_instance.name,
            "message": "File content updated successfully"
        })