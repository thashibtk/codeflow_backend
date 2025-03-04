from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Meeting
from projects.models import Project, ProjectCollaborator 
from .serializers import MeetingSerializer

class CreateMeetingView(generics.CreateAPIView):
    serializer_class = MeetingSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        project_id = self.kwargs.get("project_id")
        project = get_object_or_404(Project, id=project_id)

        # ✅ Check if user is project creator or a collaborator
        is_collaborator = ProjectCollaborator.objects.filter(project=project, user=request.user).exists()
        if not (is_collaborator or request.user == project.creator):
            return Response({"error": "You are not part of this project"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data["project"] = project.id

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            meeting = serializer.save()
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

        meeting.participants.add(request.user)
        return Response({"message": "You have joined the meeting."}, status=status.HTTP_200_OK)
