from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Meeting
from projects.models import Project, ProjectCollaborator 
from .serializers import MeetingSerializer
import random
import requests
from rest_framework.views import APIView
from django.conf import settings


DAILY_API_URL = "https://api.daily.co/v1/rooms"
DAILY_API_KEY = settings.DAILY_API_KEY 

import logging

logger = logging.getLogger(__name__)  # Add logging
class CreateMeetingView(generics.CreateAPIView):
    serializer_class = MeetingSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        project_id = self.kwargs.get("project_id")
        project = get_object_or_404(Project, id=project_id)

        # Check user permissions
        is_collaborator = ProjectCollaborator.objects.filter(project=project, user=request.user).exists()
        if not (is_collaborator or request.user == project.creator):
            return Response({"error": "You are not part of this project"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data["project"] = project.id

        # Generate a Daily.co room
        headers = {"Authorization": f"Bearer {DAILY_API_KEY}"}
        room_name = f"cf-{project.id}-{random.randint(1000, 9999)}"
        daily_payload = {"name": room_name, "privacy": "public"}

        try:
            daily_response = requests.post(DAILY_API_URL, json=daily_payload, headers=headers)
            daily_response.raise_for_status()

            room_data = daily_response.json()
            room_url = room_data.get("url")

            if not room_url:
                logger.error(f"No URL in Daily.co response: {room_data}")
                return Response({"error": "Invalid response from meeting service"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # ✅ Store just the base URL
            data["room_url"] = room_url
            logger.info(f"Successfully created Daily.co room: {room_url}")

        except Exception as e:
            logger.error(f"Failed to create Daily.co room: {str(e)}")
            return Response({"error": "Failed to create meeting room"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Validate and save the meeting
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            meeting = serializer.save(created_by=request.user)
            
            # If you want to override the auto-generated meeting_code
            meeting.meeting_code = f"CF-{random.randint(1000, 9999)}"
            
            # Double-check the room_url is set
            if not meeting.room_url and room_url:
                meeting.room_url = room_url
                
            meeting.save()
            return Response(MeetingSerializer(meeting).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListUpcomingMeetingsView(generics.ListAPIView):
    serializer_class = MeetingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Meeting.objects.filter(
            participants=self.request.user,
            scheduled_time__gte=timezone.now()
        ).order_by("scheduled_time")


class JoinMeetingView(generics.UpdateAPIView):
    serializer_class = MeetingSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        meeting_code = request.data.get("meeting_code")
        meeting = get_object_or_404(Meeting, meeting_code=meeting_code)

        # Allow any user to join (external participants)
        meeting.participants.add(request.user)
        return Response({
            "message": "You have joined the meeting.",
            "meeting": MeetingSerializer(meeting, context={"request": request}).data
        }, status=status.HTTP_200_OK)


# Add these new views for meeting management
from django.db.models import Q

class MeetingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MeetingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Meeting.objects.filter(
            Q(project__creator=self.request.user) | 
            Q(participants=self.request.user)
        ).distinct()
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            logger.info(f"Updating Meeting ID {instance.id} with data: {request.data}")

            # Check if user is meeting creator, project creator, or has edit permissions
            if (request.user != instance.created_by and  # Add this check for meeting creator
                request.user != instance.project.creator):
                is_collaborator = ProjectCollaborator.objects.filter(
                    project=instance.project,
                    user=request.user,
                    can_edit=True
                ).exists()
                if not is_collaborator:
                    logger.warning(f"User {request.user} does not have permission to update meeting {instance.id}")
                    return Response(
                        {"error": "You don't have permission to edit this meeting"},
                        status=status.HTTP_403_FORBIDDEN
                    )

            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                updated_meeting = serializer.save()
                logger.info(f"Meeting {updated_meeting.id} updated successfully.")
                return Response(serializer.data)
            
            logger.error(f"Meeting update failed. Errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error updating meeting {kwargs.get('pk')}: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Failed to update meeting: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if user is the meeting creator, project creator, or has delete permissions
        if (request.user != instance.created_by and  # Add this check for meeting creator
            request.user != instance.project.creator):
            is_collaborator = ProjectCollaborator.objects.filter(
                project=instance.project,
                user=request.user,
                can_edit=True  # Assuming edit permission includes delete
            ).exists()
            
            if not is_collaborator:
                return Response(
                    {"error": "You don't have permission to delete this meeting"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        try:
            # Delete the Daily.co room if it exists
            if instance.room_url:
                room_name = instance.room_url.split('/')[-1]
                headers = {"Authorization": f"Bearer {DAILY_API_KEY}"}
                try:
                    requests.delete(f"{DAILY_API_URL}/{room_name}", headers=headers)
                except Exception as e:
                    # Log the error but continue with deletion
                    logger.error(f"Failed to delete Daily.co room: {str(e)}")
            
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting meeting {instance.id}: {str(e)}")
            return Response(
                {"error": f"Failed to delete meeting: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
 
class StartMeetingView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        meeting = get_object_or_404(Meeting, id=pk)

        if request.user != meeting.created_by and request.user not in meeting.participants.all():
            return Response({'error': 'You are not authorized to start this meeting'}, status=403)

        meeting.is_started = True
        meeting.save()
        
        return Response({
            'message': 'Meeting started successfully',
            'room_url': meeting.room_url
        })
