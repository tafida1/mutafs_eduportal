from django.conf import settings
from django.db import models


class ParentProfile(models.Model):
    class Relationship(models.TextChoices):
        FATHER = "FATHER", "Father"
        MOTHER = "MOTHER", "Mother"
        GUARDIAN = "GUARDIAN", "Guardian"
        OTHER = "OTHER", "Other"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parent_profile",
    )

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="parents",
    )

    children = models.ManyToManyField(
        "students.StudentProfile",
        related_name="parents",
        blank=True,
    )

    relationship = models.CharField(
        max_length=20,
        choices=Relationship.choices,
        default=Relationship.GUARDIAN,
    )

    phone = models.CharField(max_length=30)
    alternate_phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)

    occupation = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__last_name", "user__first_name"]
        indexes = [
            models.Index(fields=["school", "is_active"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username