from django.contrib import admin
from .models import CBTQuestion, CBTExam, CBTAttempt, CBTAttemptQuestion


@admin.register(CBTQuestion)
class CBTQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "school_class",
        "school",
        "difficulty",
        "correct_option",
        "is_active",
        "created_at",
    )
    list_filter = ("school", "school_class", "subject", "difficulty", "is_active")
    search_fields = ("question_text", "option_a", "option_b", "option_c", "option_d")


@admin.register(CBTExam)
class CBTExamAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "school",
        "school_class",
        "subject",
        "duration_minutes",
        "total_questions",
        "is_active",
        "created_at",
    )
    list_filter = ("school", "school_class", "subject", "session", "term", "is_active")
    search_fields = ("title",)
    filter_horizontal = ("questions",)


class CBTAttemptQuestionInline(admin.TabularInline):
    model = CBTAttemptQuestion
    extra = 0
    readonly_fields = ("question", "selected_option", "is_correct")


@admin.register(CBTAttempt)
class CBTAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "exam",
        "school",
        "score",
        "percentage",
        "status",
        "started_at",
        "submitted_at",
    )
    list_filter = ("school", "exam", "status", "started_at")
    search_fields = ("student__surname", "student__first_name", "student__admission_number", "exam__title")
    inlines = [CBTAttemptQuestionInline]