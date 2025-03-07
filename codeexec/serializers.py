from rest_framework import serializers
from .models import CodeExecution

class CodeExecutionRequestSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=CodeExecution.LANGUAGE_CHOICES)
    code = serializers.CharField()
    project_id = serializers.UUIDField()
    files = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    command = serializers.CharField(required=False, allow_blank=True)

class CodeExecutionResultSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeExecution
        fields = ['id', 'language', 'code', 'command', 'stdout', 'stderr', 
                 'exit_code', 'execution_time', 'created_at', 'user_name']
    
    def get_user_name(self, obj):
        return obj.user.email