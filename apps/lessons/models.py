from django.conf import settings
from django.db import models


class LessonResource(models.Model):
    class ResourceType(models.TextChoices):
        LESSON_NOTE = "LESSON_NOTE", "Lesson Note"
        ASSIGNMENT = "ASSIGNMENT", "Assignment"
        PRESENTATION = "PRESENTATION", "Presentation"
        VIDEO_LINK = "VIDEO_LINK", "Video Link"
        OTHER = "OTHER", "Other"

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="lesson_resources",
    )
    title = models.CharField(max_length=255)

    resource_type = models.CharField(
        max_length=30,
        choices=ResourceType.choices,
        default=ResourceType.LESSON_NOTE,
    )

    session = models.ForeignKey(
        "academics.AcademicSession",
        on_delete=models.CASCADE,
        related_name="lesson_resources",
    )
    term = models.ForeignKey(
        "academics.AcademicTerm",
        on_delete=models.CASCADE,
        related_name="lesson_resources",
    )
    school_class = models.ForeignKey(
        "academics.SchoolClass",
        on_delete=models.CASCADE,
        related_name="lesson_resources",
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.CASCADE,
        related_name="lesson_resources",
    )

    description = models.TextField(blank=True)
    file = models.FileField(upload_to="lesson_resources/", blank=True, null=True)
    external_link = models.URLField(blank=True)

    is_published = models.BooleanField(default=True)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_lesson_resources",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school", "school_class", "subject"]),
            models.Index(fields=["session", "term"]),
            models.Index(fields=["is_published"]),
        ]

    def __str__(self):
        return self.title