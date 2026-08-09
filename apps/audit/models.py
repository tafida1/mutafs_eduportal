from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        LOGIN_SUCCESS = "LOGIN_SUCCESS", "Login Success"
        LOGIN_FAILED = "LOGIN_FAILED", "Login Failed"
        LOGOUT = "LOGOUT", "Logout"

        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"
        VIEW = "VIEW", "View"
        EXPORT = "EXPORT", "Export"

        SCHOOL_ENABLED = "SCHOOL_ENABLED", "School Enabled"
        SCHOOL_DISABLED = "SCHOOL_DISABLED", "School Disabled"

        SUBSCRIPTION_UPDATED = "SUBSCRIPTION_UPDATED", "Subscription Updated"

        RESULT_PUBLISHED = "RESULT_PUBLISHED", "Result Published"
        RESULT_UNPUBLISHED = "RESULT_UNPUBLISHED", "Result Unpublished"

        CBT_SUBMITTED = "CBT_SUBMITTED", "CBT Submitted"

        SECURITY_BLOCK = "SECURITY_BLOCK", "Security Block"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    action = models.CharField(max_length=50, choices=Action.choices, db_index=True)
    module = models.CharField(max_length=100, blank=True, db_index=True)

    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)

    description = models.TextField(blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school", "created_at"]),
            models.Index(fields=["actor", "created_at"]),
            models.Index(fields=["action"]),
            models.Index(fields=["module"]),
        ]

    def __str__(self):
        return f"{self.action} - {self.actor} - {self.created_at}"