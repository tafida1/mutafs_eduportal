from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "school",
        "is_active",
        "is_staff",
        "last_login",
    )
    list_filter = (
        "role",
        "school",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "phone",
        "school__name",
    )
    ordering = ("username",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Mutafs EduPortal SaaS Fields",
            {
                "fields": (
                    "role",
                    "school",
                    "phone",
                    "must_change_password",
                    "last_login_ip",
                    "last_activity_at",
                    "failed_login_attempts",
                )
            },
        ),
    )

    readonly_fields = (
        "last_login_ip",
        "last_activity_at",
        "failed_login_attempts",
    )