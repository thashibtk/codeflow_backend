import json
from channels.generic.websocket import AsyncWebsocketConsumer

class CollaboratorConsumer(AsyncWebsocketConsumer):
    active_collaborators = set()  # Store active collaborators

    async def connect(self):
        self.user_id = self.scope["path_remaining"]  # Extract user ID from the URL
        self.room_group_name = "collaborators"

        # Add user to active collaborators
        self.active_collaborators.add(self.user_id)

        # Join group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Broadcast updated collaborator list
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "collaborator.update",
                "collaborators": list(self.active_collaborators),
            },
        )

    async def disconnect(self, close_code):
        # Remove user from active collaborators
        self.active_collaborators.discard(self.user_id)

        # Leave group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Broadcast updated collaborator list
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "collaborator.update",
                "collaborators": list(self.active_collaborators),
            },
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "")

        # Broadcast message to all collaborators
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": message,
                "sender": self.user_id,
            },
        )

    async def collaborator_update(self, event):
        # Send updated collaborator list to all clients
        await self.send(text_data=json.dumps({"type": "collaborators", "users": event["collaborators"]}))

    async def chat_message(self, event):
        # Send chat message to all clients
        await self.send(text_data=json.dumps({"type": "chat", "message": event["message"], "sender": event["sender"]}))
