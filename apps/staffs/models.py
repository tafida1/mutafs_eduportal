from django.conf import settings
from django.db import models


class StaffProfile(models.Model):
    class StaffType(models.TextChoices):
        TEACHING = "TEACHING", "Teaching Staff"
        NON_TEACHING = "NON_TEACHING", "Non-Teaching Staff"

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"
        RESIGNED = "RESIGNED", "Resigned"
        TERMINATED = "TERMINATED", "Terminated"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="staff_members",
    )

    staff_type = models.CharField(
        max_length=20,
        choices=StaffType.choices,
        default=StaffType.TEACHING,
    )

    staff_id = models.CharField(max_length=50, unique=True, db_index=True)

    gender = models.CharField(max_length=10, choices=Gender.choices)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)

    designation = models.CharField(max_length=150, blank=True)
    qualification = models.CharField(max_length=150, blank=True)

    assigned_classes = models.ManyToManyField(
        "academics.SchoolClass",
        related_name="assigned_staff",
        blank=True,
    )

    assigned_subjects = models.ManyToManyField(
        "academics.Subject",
        related_name="assigned_staff",
        blank=True,
    )

    passport = models.ImageField(upload_to="staff_passports/", blank=True, null=True)

    employment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__first_name", "user__last_name"]
        indexes = [
            models.Index(fields=["school", "staff_type"]),
            models.Index(fields=["school", "status"]),
            models.Index(fields=["staff_id"]),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.staff_id}"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @staticmethod
    def generate_staff_id(school):
        prefix = school.code.upper() if school and school.code else "MUTAFS"
        count = StaffProfile.objects.filter(school=school).count() + 1
        return f"{prefix}/STAFF/{count:04d}"