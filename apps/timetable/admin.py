from django.contrib import admin
from .models import TimeSlot, TimetableEntry


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = (
        "school",
        "day",
        "start_time",
        "end_time",
        "label",
        "is_break",
        "is_active",
    )
    list_filter = ("school", "day", "is_break", "is_active")
    search_fields = ("school__name", "label")


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = (
        "school",
        "school_class",
        "time_slot",
        "subject",
        "teacher",
        "room",
        "is_active",
    )
    list_filter = (
        "school",
        "school_class",
        "subject",
        "teacher",
        "is_active",
    )
    search_fields = (
        "school_class__name",
        "subject__name",
        "teacher__user__first_name",
        "teacher__user__last_name",
        "room",
    )
    readonly_fields = ("created_at", "updated_at")