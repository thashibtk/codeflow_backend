from django.urls import path
from meetings.views import (
    CreateMeetingView, ListUpcomingMeetingsView, JoinMeetingView, MeetingDetailView, StartMeetingView
)

urlpatterns = [
    path("<uuid:project_id>/create-meeting/", CreateMeetingView.as_view(), name="create_meeting"),
    path("", ListUpcomingMeetingsView.as_view(), name="upcoming_meetings"),
    path("join/", JoinMeetingView.as_view(), name="join_meeting"),
    path('<int:pk>/', MeetingDetailView.as_view(), name='meeting-detail'),

    # ✅ Add this line
    path('<int:pk>/start/', StartMeetingView.as_view(), name='start_meeting'),
]


# import requests

# DAILY_API_KEY = "9e2a0078e67fa6a00ebe89830f8520341dd65719505d533fa99555a62ec41104"
# DAILY_API_URL = "https://api.daily.co/v1/rooms"

# headers = {
#     "Authorization": f"Bearer {DAILY_API_KEY}",
#     "Content-Type": "application/json"
# }

# response = requests.get(DAILY_API_URL, headers=headers)

# print(response.status_code, response.text)
# data = {
#     "name": "test-room", 
#     "privacy": "public"
# }