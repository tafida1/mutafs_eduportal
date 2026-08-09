from django.contrib import admin

from .models import Announcement, UserNotification


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "school",
        "audience",
        "is_pinned",
        "is_active",
        "publish_at",
        "expires_at",
        "created_by",
    )

    list_filter = (
        "school",
        "audience",
        "is_pinned",
        "is_active",
    )

    search_fields = (
        "title",
        "message",
    )


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "announcement",
        "is_read",
        "read_at",
    )

    list_filter = (
        "is_read",
    )