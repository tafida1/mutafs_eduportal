from django.contrib import admin
from .models import ParentProfile


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "school",
        "relationship",
        "phone",
        "is_active",
        "created_at",
    )
    list_filter = (
        "school",
        "relationship",
        "is_active",
        "created_at",
    )
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone",
        "alternate_phone",
        "children__surname",
        "children__first_name",
        "children__admission_number",
    )
    filter_horizontal = ("children",)
    readonly_fields = ("created_at", "updated_at")