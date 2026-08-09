from django.contrib import admin
from .models import LessonResource


@admin.register(LessonResource)
class LessonResourceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "school",
        "school_class",
        "subject",
        "session",
        "term",
        "resource_type",
        "is_published",
        "uploaded_by",
        "created_at",
    )
    list_filter = (
        "school",
        "school_class",
        "subject",
        "session",
        "term",
        "resource_type",
        "is_published",
    )
    search_fields = (
        "title",
        "description",
        "school__name",
        "subject__name",
        "school_class__name",
    )
    readonly_fields = ("created_at", "updated_at")