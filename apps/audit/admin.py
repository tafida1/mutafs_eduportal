from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "action",
        "module",
        "actor",
        "school",
        "ip_address",
        "created_at",
    )
    list_filter = (
        "action",
        "module",
        "school",
        "created_at",
    )
    search_fields = (
        "actor__username",
        "actor__email",
        "school__name",
        "description",
        "ip_address",
    )
    readonly_fields = (
        "actor",
        "school",
        "action",
        "module",
        "object_type",
        "object_id",
        "description",
        "ip_address",
        "user_agent",
        "created_at",
    )

    def has_add_permission(self, request):
        return False