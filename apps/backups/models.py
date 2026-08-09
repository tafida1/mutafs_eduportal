from django.conf import settings
from django.db import models


class BackupLog(models.Model):
    class BackupType(models.TextChoices):
        DATABASE = "DATABASE", "Database"
        MEDIA = "MEDIA", "Media Files"
        SCHOOL_EXPORT = "SCHOOL_EXPORT", "School Export"
        FULL_SYSTEM = "FULL_SYSTEM", "Full System"

    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    backup_type = models.CharField(max_length=30, choices=BackupType.choices)
    status = models.CharField(max_length=20, choices=Status.choices)
    file_path = models.CharField(max_length=500, blank=True)
    message = models.TextField(blank=True)

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="backup_logs",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_backup_logs",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_backup_type_display()} - {self.get_status_display()}"