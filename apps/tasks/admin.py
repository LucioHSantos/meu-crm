from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'priority', 'task_type', 'due_date', 'assigned_to', 'contact']
    list_filter = ['status', 'priority', 'task_type', 'due_date']
    search_fields = ['title', 'description']
    list_editable = ['status', 'priority']
    ordering = ['due_date', '-priority']
    readonly_fields = ['created_at', 'updated_at']
