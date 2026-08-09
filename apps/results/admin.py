from django.contrib import admin
from .models import GradeScale, ResultEntry


@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = ("school", "grade", "min_score", "max_score", "remark")
    list_filter = ("school", "grade")
    search_fields = ("school__name", "grade", "remark")


@admin.register(ResultEntry)
class ResultEntryAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "school",
        "school_class",
        "session",
        "term",
        "subject",
        "ca_score",
        "exam_score",
        "total_score",
        "grade",
        "is_published",
    )
    list_filter = (
        "school",
        "school_class",
        "session",
        "term",
        "subject",
        "is_published",
    )
    search_fields = (
        "student__surname",
        "student__first_name",
        "student__admission_number",
        "subject__name",
    )
    readonly_fields = ("total_score", "grade", "remark", "created_at", "updated_at")