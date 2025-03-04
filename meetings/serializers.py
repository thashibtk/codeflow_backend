from rest_framework import serializers
from .models import Meeting

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Meeting, Project

User = get_user_model()

class MeetingSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    meeting_code = serializers.ReadOnlyField()

    class Meta:
        model = Meeting
        fields = ["id", "name", "project", "scheduled_time", "participants", "meeting_code", "created_at"]
        read_only_fields = ["id", "meeting_code", "created_at"]

    def create(self, validated_data):
        project = validated_data.get("project")

        participants_data = validated_data.pop('participants', [])
        meeting = Meeting.objects.create(**validated_data)
        
        default_participants = [collaborator.user.id for collaborator in project.collaborators.all()]
        
        participants_to_set = [user.id for user in participants_data] if participants_data else default_participants
        meeting.participants.set(participants_to_set)
        
        return meeting

       
