from django.db import models
from django.contrib.auth import get_user_model
from projects.models import Project
import uuid

User = get_user_model()

class CodeExecution(models.Model):
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('typescript', 'TypeScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('c', 'C'),
        ('ruby', 'Ruby'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('php', 'PHP'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, related_name='code_executions', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='code_executions', on_delete=models.CASCADE)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    code = models.TextField()
    command = models.CharField(max_length=255, blank=True, null=True)
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    exit_code = models.IntegerField(default=0)
    execution_time = models.FloatField(default=0.0)  # in seconds
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.language} execution by {self.user.username} in {self.project.name}"
