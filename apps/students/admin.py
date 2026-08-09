from django.contrib import admin
from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "admission_number",
        "school",
        "current_class",
        "gender",
        "status",
        "created_at",
    )
    list_filter = (
        "school",
        "current_class",
        "gender",
        "status",
        "created_at",
    )
    search_fields = (
        "surname",
        "first_name",
        "middle_name",
        "admission_number",
        "passkey",
        "guardian_phone",
        "user__username",
        "user__email",
    )
    readonly_fields = (
        "admission_number",
        "passkey",
        "created_at",
        "updated_at",
    )