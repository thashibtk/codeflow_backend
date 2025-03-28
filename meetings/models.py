from django.db import models
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.utils import timezone
from projects.models import Project  # ✅ Import from the projects app

User = get_user_model()

class Meeting(models.Model):
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name="meetings"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="created_meetings"
    )
    name = models.CharField(max_length=255) 
    description = models.TextField(blank=True, null=True) 
    scheduled_time = models.DateTimeField()
    participants = models.ManyToManyField(User, related_name="meetings")
    meeting_code = models.CharField(max_length=10, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_started = models.BooleanField(default=False)
    room_url = models.URLField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.meeting_code:
            self.meeting_code = get_random_string(8)
        super().save(*args, **kwargs)
