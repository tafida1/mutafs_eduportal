from django.conf import settings
from django.db import models
from django.utils import timezone


class Announcement(models.Model):

    class Audience(models.TextChoices):
        ALL = "ALL", "All Users"
        TEACHERS = "TEACHERS", "Teachers"
        STUDENTS = "STUDENTS", "Students"
        PARENTS = "PARENTS", "Parents"
        SCHOOL_ADMINS = "SCHOOL_ADMINS", "School Admins"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="announcements",
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    audience = models.CharField(
        max_length=30,
        choices=Audience.choices,
        default=Audience.ALL,
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )

    attachment = models.FileField(
        upload_to="announcements/",
        blank=True,
        null=True,
    )

    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    publish_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_announcements",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_pinned", "-publish_at"]
        indexes = [
            models.Index(fields=["school", "audience"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["publish_at"]),
        ]

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class UserNotification(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name="user_notifications",
    )

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "announcement")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.announcement}"
