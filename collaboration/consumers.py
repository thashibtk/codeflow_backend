import json
from channels.generic.websocket import AsyncWebsocketConsumer
from collections import defaultdict

class CollaboratorConsumer(AsyncWebsocketConsumer):
    # Class-level storage for active users and file content
    active_collaborators = {}  # Stores active collaborators per project
    file_collaborators = defaultdict(set)  # Stores users per file
    file_content = {}  # Stores the latest content per file
    file_versions = defaultdict(lambda: 1)  # Stores current version per file
    cursor_positions = {}  # Stores cursor positions per user per file
    
    async def connect(self):
        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]
        self.room_group_name = f"collaborators_{self.project_id}"
        self.user_name = "Anonymous"
        self.current_file_id = None

        # Ensure active collaborators exist for this project
        if self.room_group_name not in self.active_collaborators:
            self.active_collaborators[self.room_group_name] = set()

        # Join the project group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Add user to active collaborators
        self.active_collaborators[self.room_group_name].add(self.user_name)

        # Send updated list of collaborators
        await self.broadcast_collaborators()
        
        # Debug log
        print(f"WebSocket connected: {self.room_group_name}, User: {self.user_name}")

    async def disconnect(self, close_code):
        # Remove user from file collaborators if they were editing a file
        if self.current_file_id:
            file_key = f"{self.project_id}_{self.current_file_id}"
            self.file_collaborators[file_key].discard(self.user_name)
            
            # Remove cursor position for this user
            if file_key in self.cursor_positions:
                if self.user_name in self.cursor_positions[file_key]:
                    del self.cursor_positions[file_key][self.user_name]
        
        # Remove this user from the active list
        if self.room_group_name in self.active_collaborators:
            self.active_collaborators[self.room_group_name].discard(self.user_name)

            # If no more users are in the project, clean up
            if not self.active_collaborators[self.room_group_name]:
                del self.active_collaborators[self.room_group_name]

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.broadcast_collaborators()
        
        # Debug log
        print(f"WebSocket disconnected: {self.room_group_name}, User: {self.user_name}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type", "")
        
        # Debug log
        print(f"Received message: {message_type} from {data.get('sender', 'Unknown')}")
        
        if message_type == "identify":
            # User identified themselves and the file they're working on
            sender = data.get("sender", "Anonymous")
            file_id = data.get("file_id")
            
            # Update user information
            self.user_name = sender
            self.current_file_id = file_id
            
            # Update active collaborators
            if self.room_group_name in self.active_collaborators:
                self.active_collaborators[self.room_group_name].discard("Anonymous")
                self.active_collaborators[self.room_group_name].add(sender)
            
            # Add user to file collaborators
            if file_id:
                file_key = f"{self.project_id}_{file_id}"
                self.file_collaborators[file_key].add(sender)
                
                # Send current cursor positions for this file to the new user
                if file_key in self.cursor_positions:
                    for user, position in self.cursor_positions[file_key].items():
                        if user != sender:  # Don't send own cursor back
                            await self.send(text_data=json.dumps({
                                "type": "cursor_update",
                                "file_id": file_id,
                                "sender": user,
                                "position": position
                            }))
            
            # Broadcast updated collaborator list
            await self.broadcast_collaborators()
            
        elif message_type == "chat":
            # Handle chat messages similar to before
            message = data.get("message", "")
            sender = data.get("sender", "Anonymous")
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender": sender,
                },
            )
            
        elif message_type == "code_update":
            # Handle code updates
            file_id = data.get("file_id")
            sender = data.get("sender", "Anonymous")
            content = data.get("content", "")
            
            if file_id:
                file_key = f"{self.project_id}_{file_id}"
                # Update the stored content for this file
                self.file_content[file_key] = content
                # Increment version
                self.file_versions[file_key] += 1
                
                # Broadcast the code update to all clients
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "code_update",
                        "file_id": file_id,
                        "sender": sender,
                        "content": content,
                        "version": self.file_versions[file_key]
                    },
                )
                
        elif message_type == "cursor_update":
            # Handle cursor position updates
            file_id = data.get("file_id")
            sender = data.get("sender", "Anonymous")
            position = data.get("position", {})
            
            if file_id:
                # Store cursor position for this user
                file_key = f"{self.project_id}_{file_id}"
                if file_key not in self.cursor_positions:
                    self.cursor_positions[file_key] = {}
                
                self.cursor_positions[file_key][sender] = position
                
                # Broadcast cursor position to all clients
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "cursor_update",
                        "file_id": file_id,
                        "sender": sender,
                        "position": position
                    },
                )
                
        elif message_type == "request_content":
            # Handle requests for latest file content
            file_id = data.get("file_id")
            
            if file_id:
                file_key = f"{self.project_id}_{file_id}"
                if file_key in self.file_content:
                    # Send current content back to the requesting client
                    await self.send(text_data=json.dumps({
                        "type": "full_content",
                        "file_id": file_id,
                        "content": self.file_content[file_key],
                        "version": self.file_versions[file_key]
                    }))
                    
        elif message_type == "file_saved":
            # Handle file save notifications
            file_id = data.get("file_id")
            sender = data.get("sender", "Anonymous")
            version = data.get("version", 1)
            
            if file_id:
                file_key = f"{self.project_id}_{file_id}"
                # Update the version number
                self.file_versions[file_key] = version
                
                # Notify all clients that the file was saved
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "file_saved",
                        "file_id": file_id,
                        "sender": sender,
                        "version": version
                    },
                )

    async def broadcast_collaborators(self):
        """Send updated collaborator list to all clients."""
        if self.room_group_name in self.active_collaborators:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "collaborator_update",
                    "collaborators": list(self.active_collaborators[self.room_group_name]),
                },
            )

    async def collaborator_update(self, event):
        """Send collaborator update to clients."""
        await self.send(text_data=json.dumps({
            "type": "collaborators",
            "users": event["collaborators"]
        }))

    async def chat_message(self, event):
        """Send chat messages to all clients."""
        await self.send(text_data=json.dumps({
            "type": "chat",
            "message": event["message"],
            "sender": event["sender"]
        }))
        
    async def code_update(self, event):
        """Send code updates to all clients."""
        await self.send(text_data=json.dumps({
            "type": "code_update",
            "file_id": event["file_id"],
            "sender": event["sender"],
            "content": event["content"],
            "version": event["version"]
        }))
        
    async def cursor_update(self, event):
        """Send cursor position updates to all clients."""
        await self.send(text_data=json.dumps({
            "type": "cursor_update",
            "file_id": event["file_id"],
            "sender": event["sender"],
            "position": event["position"]
        }))
        
    async def file_saved(self, event):
        """Send file saved notifications to all clients."""
        await self.send(text_data=json.dumps({
            "type": "file_saved",
            "file_id": event["file_id"],
            "sender": event["sender"],
            "version": event["version"]
        }))