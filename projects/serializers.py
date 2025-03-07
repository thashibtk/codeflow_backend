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
            "project": {"required": False} 
        }

    def validate(self, data):
        if not data.get("name"):
            raise serializers.ValidationError({"name": "File name is required"})

        if not data.get("is_folder") and "content" not in data:
            raise serializers.ValidationError({"content": "File content is required"})

        project = data.get("project", self.instance.project if self.instance else None)
        parent_folder = data.get("parent_folder", self.instance.parent_folder if self.instance else None)
        name = data["name"]

        
        existing_file = File.objects.filter(
            project=project,
            parent_folder=parent_folder,
            name=name
        ).exclude(id=self.instance.id if self.instance else None)

        if existing_file.exists():
            raise serializers.ValidationError({"name": "A file or folder with this name already exists in this location."})

        return data

