# codeexec/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import CodeExecution
from .serializers import CodeExecutionRequestSerializer, CodeExecutionResultSerializer
from projects.models import Project
from .execution import execute_code
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from projects.models import ProjectCollaborator 

class CodeExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retrieving code execution results.
    """
    serializer_class = CodeExecutionResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Get executions for projects the user has access to
        return CodeExecution.objects.filter(
            project__in=Project.objects.filter(members=user)
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_code_view(request):
    """
    Execute code in a Docker container and return the results.
    """
    serializer = CodeExecutionRequestSerializer(data=request.data)
    if serializer.is_valid():
        project_id = serializer.validated_data['project_id']
        project = get_object_or_404(Project, id=project_id)

        # ✅ Corrected: Check if user is a collaborator
        if not ProjectCollaborator.objects.filter(project=project, user=request.user).exists():
            return Response(
                {"error": "You do not have access to this project"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        language = serializer.validated_data['language']
        code = serializer.validated_data['code']
        command = serializer.validated_data.get('command', '')

        # Execute the code
        stdout, stderr, exit_code, execution_time = execute_code(
            language, code, command
        )

        # Save execution result
        result = CodeExecution.objects.create(
            project=project,
            user=request.user,
            language=language,
            code=code,
            command=command,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            execution_time=execution_time
        )

        # Send notification over WebSocket
        channel_layer = get_channel_layer()
        group_name = f"project_{project_id}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'code_executed',
                'message': {
                    'type': 'code_execution',
                    'execution_id': str(result.id),
                    'user': request.user.email,
                    'language': language,
                    'stdout': stdout[:200] + '...' if len(stdout) > 200 else stdout,
                    'has_error': exit_code != 0 or bool(stderr),
                }
            }
        )

        result_serializer = CodeExecutionResultSerializer(result)
        return Response(result_serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
