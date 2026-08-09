from django.contrib import admin
from .models import BackupLog


@admin.register(BackupLog)
class BackupLogAdmin(admin.ModelAdmin):
    list_display = (
        "backup_type",
        "status",
        "school",
        "created_by",
        "created_at",
    )
    list_filter = ("backup_type", "status", "created_at")
    search_fields = ("file_path", "message", "school__name")
    readonly_fields = ("created_at",)