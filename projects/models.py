from django.db import models
from django.contrib.auth import get_user_model
import uuid
import random
import string

User = get_user_model()

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_projects")
    project_code = models.CharField(max_length=10, unique=True, default=generate_code)
    created_at = models.DateTimeField(auto_now_add=True)

class ProjectCollaborator(models.Model):
    VIEW = "view"
    EDIT = "edit"

    PERMISSION_CHOICES = [
        (VIEW, "View"),
        (EDIT, "Edit"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="collaborators")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="collaborations")
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default=VIEW)

    class Meta:
        unique_together = ("project", "user")

# 📂 File Model for File Explorer
class File(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="files")
    name = models.CharField(max_length=255)
    is_folder = models.BooleanField(default=False)
    content = models.TextField(blank=True, null=True)  # Only for files
    parent_folder = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")

    def __str__(self):
        return f"{'📁' if self.is_folder else '📄'} {self.name}"
