from django.contrib import admin
from .models import StudentAttendance, StaffAttendance


@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "school",
        "school_class",
        "date",
        "status",
        "marked_by",
        "created_at",
    )
    list_filter = (
        "school",
        "school_class",
        "status",
        "date",
    )
    search_fields = (
        "student__surname",
        "student__first_name",
        "student__admission_number",
        "remarks",
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "staff",
        "school",
        "date",
        "status",
        "marked_by",
        "created_at",
    )
    list_filter = (
        "school",
        "status",
        "date",
    )
    search_fields = (
        "staff__staff_id",
        "staff__user__first_name",
        "staff__user__last_name",
        "remarks",
    )
    readonly_fields = ("created_at", "updated_at")