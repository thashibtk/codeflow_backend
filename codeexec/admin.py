from django.contrib import admin
from .models import CodeExecution

@admin.register(CodeExecution)
class CodeExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'user', 'language', 'exit_code', 'execution_time', 'created_at')
    list_filter = ('language', 'exit_code', 'created_at')
    search_fields = ('user__username', 'project__name', 'code')
    readonly_fields = ('id', 'created_at', 'exit_code', 'execution_time')
    date_hierarchy = 'created_at'