from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Meeting
from projects.models import Project

User = get_user_model()

class MeetingSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    meeting_code = serializers.ReadOnlyField()
    project_name = serializers.SerializerMethodField()
    creator_name = serializers.SerializerMethodField()
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    description = serializers.CharField(required=False, allow_blank=True)
    is_creator = serializers.SerializerMethodField()
    is_collaborator = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = [
            "id", "name", "description", "project", "project_name", 
            "scheduled_time", "participants", "meeting_code", 
            "created_at", "creator_name", "created_by", "is_started",
            "is_creator", "is_collaborator", "room_url" 
        ]
        read_only_fields = [
            "id", "meeting_code", "created_at", "project_name", 
            "creator_name", "created_by", "is_creator", "is_collaborator", "room_url"
        ]


    def get_project_name(self, obj):
        return obj.project.name if obj.project else None

    def get_creator_name(self, obj):
        return obj.created_by.full_name if obj.created_by else None  # 🔄 Fixed from obj.project.creator

    def get_is_creator(self, obj):
        request = self.context.get("request")
        return request.user == obj.created_by if request else False

    def get_is_collaborator(self, obj):
        request = self.context.get("request")
        return request.user in obj.participants.all() if request else False

    def create(self, validated_data):
        project = validated_data.get("project")
        participants_data = validated_data.pop('participants', [])
        meeting = Meeting.objects.create(**validated_data)

        # Add project collaborators as participants
        if project:
            default_participants = [project.creator.id]
            default_participants.extend([
                collaborator.user.id for collaborator in project.collaborators.all()
            ])
            
            participants_to_set = list(set(
                [user.id for user in participants_data] if participants_data else default_participants
            ))
            meeting.participants.set(participants_to_set)

        return meeting
        
    def to_representation(self, instance):
        """Format scheduled_time for better display"""
        representation = super().to_representation(instance)
        
        # Format the datetime for better display, but keep ISO format for API response
        # This ensures consistency while still being parsable on the frontend
        if representation['scheduled_time']:
            # Keep the ISO format, frontend will handle display formatting
            pass
            
        return representation