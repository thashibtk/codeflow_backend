# codeexec/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from projects.models import Project

class CodeExecutionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.group_name = f"project_{self.project_id}"
        
        # Get user from scope
        user = self.scope["user"]
        
        # Anonymous users can't connect
        if user.is_anonymous:
            await self.close()
            return
        
        # Check if user has access to the project
        has_access = await self.check_project_access(user)
        if not has_access:
            await self.close()
            return
        
        # Join the project group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify others that user joined
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "user_joined",
                "message": {
                    "type": "user_joined",
                    "user_id": str(user.id),
                    "username": user.username
                }
            }
        )
    
    async def disconnect(self, close_code):
        # Leave the project group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            
            # Notify others that user left
            user = self.scope["user"]
            if not user.is_anonymous:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "user_left",
                        "message": {
                            "type": "user_left",
                            "user_id": str(user.id),
                            "username": user.username
                        }
                    }
                )
    
    async def receive_json(self, content):
        message_type = content.get("type", "")
        
        # Handle different message types
        if message_type == "execute_code":
            # This could be handled via REST API
            pass
        elif message_type == "terminal_input":
            # Forward terminal input to other users
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "terminal_input",
                    "message": {
                        "type": "terminal_input",
                        "user_id": str(self.scope["user"].id),
                        "username": self.scope["user"].username,
                        "input": content.get("input", "")
                    }
                }
            )
    
    # Event handlers
    async def user_joined(self, event):
        await self.send_json(event["message"])
    
    async def user_left(self, event):
        await self.send_json(event["message"])
    
    async def terminal_input(self, event):
        await self.send_json(event["message"])
    
    async def code_executed(self, event):
        await self.send_json(event["message"])
    
    # Database access methods
    @database_sync_to_async
    def check_project_access(self, user):
        try:
            project = Project.objects.get(id=self.project_id)
            return user in project.members.all()
        except Project.DoesNotExist:
            return False
