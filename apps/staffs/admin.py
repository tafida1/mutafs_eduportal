from django.contrib import admin
from .models import StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "staff_id",
        "school",
        "staff_type",
        "designation",
        "status",
        "created_at",
    )
    list_filter = (
        "school",
        "staff_type",
        "gender",
        "status",
        "created_at",
    )
    search_fields = (
        "staff_id",
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone",
        "designation",
    )
    filter_horizontal = ("assigned_classes", "assigned_subjects")
    readonly_fields = ("staff_id", "created_at", "updated_at")