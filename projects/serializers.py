from rest_framework import serializers
from .models import Project, ProjectCollaborator, File

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "description", "creator", "project_code", "created_at"]
        read_only_fields = ["creator", "project_code", "created_at"]

class ProjectCollaboratorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCollaborator
        fields = "__all__"

# 📂 Serializer for Files/Folders
class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ["id", "project", "name", "is_folder", "content", "parent_folder"]
        extra_kwargs = {
            "project": {"required": False}  # Ensure project is not required in the request
        }

    def validate(self, data):
        if not data.get("name"):
            raise serializers.ValidationError({"name": "File name is required"})

        # Ensure content is provided for files but not required for folders
        if not data.get("is_folder") and "content" not in data:
            raise serializers.ValidationError({"content": "File content is required"})

        return data
