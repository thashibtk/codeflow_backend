from django.urls import path
from .views import CreateMeetingView, ListUpcomingMeetingsView, JoinMeetingView

urlpatterns = [
    path("<uuid:project_id>/create-meeting/", CreateMeetingView.as_view(), name="create_meeting"),
    path("", ListUpcomingMeetingsView.as_view(), name="upcoming_meetings"),
    path("join/", JoinMeetingView.as_view(), name="join_meeting"),
]
