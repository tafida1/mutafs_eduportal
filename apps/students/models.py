import secrets
import string
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_passkey(length=8):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class StudentProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        GRADUATED = "GRADUATED", "Graduated"
        TRANSFERRED = "TRANSFERRED", "Transferred"
        SUSPENDED = "SUSPENDED", "Suspended"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="students",
    )

    current_class = models.ForeignKey(
        "academics.SchoolClass",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )

    admission_number = models.CharField(max_length=50, unique=True, db_index=True)
    passkey = models.CharField(max_length=20, unique=True, db_index=True)
    result_token = models.CharField(max_length=80, unique=True, blank=True, db_index=True)
    result_qr = models.ImageField(upload_to="result_qr_codes/", blank=True, null=True)

    surname = models.CharField(max_length=100, db_index=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)

    gender = models.CharField(max_length=10, choices=Gender.choices)
    date_of_birth = models.DateField(null=True, blank=True)

    passport = models.ImageField(upload_to="student_passports/", blank=True, null=True)

    guardian_name = models.CharField(max_length=150, blank=True)
    guardian_phone = models.CharField(max_length=30, blank=True)
    guardian_email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    admission_date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["surname", "first_name"]
        indexes = [
            models.Index(fields=["school", "current_class"]),
            models.Index(fields=["school", "status"]),
            models.Index(fields=["surname"]),
            models.Index(fields=["admission_number"]),
            models.Index(fields=["passkey"]),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.admission_number}"

    @property
    def full_name(self):
        names = [self.surname, self.first_name, self.middle_name]
        return " ".join([name for name in names if name]).strip()

    @staticmethod
    def generate_admission_number(school):
        year = timezone.localdate().year
        prefix = school.code.upper() if school and school.code else "MUTAFS"

        count = StudentProfile.objects.filter(
            school=school,
            admission_date__year=year,
        ).count() + 1

        return f"{prefix}/{year}/{count:04d}"

    @staticmethod
    def generate_unique_passkey():
        while True:
            key = generate_passkey()
            if not StudentProfile.objects.filter(passkey=key).exists():
                return key

    def save(self, *args, **kwargs):
        if not self.result_token:
            self.result_token = uuid.uuid4().hex

        super().save(*args, **kwargs)

        if not self.result_qr:
            from apps.core.qr_utils import generate_qr_image

            verify_url = f"{settings.SITE_URL}/verify/result/{self.result_token}/"
            qr_file = generate_qr_image(
                verify_url,
                filename=f"student_{self.id}_result_qr.png",
            )

            self.result_qr.save(qr_file.name, qr_file, save=False)
            super().save(update_fields=["result_qr"])




class StudentClassMovement(models.Model):
    class MovementType(models.TextChoices):
        PROMOTION = "PROMOTION", "Promotion"
        DEMOTION = "DEMOTION", "Demotion"
        TRANSFER = "TRANSFER", "Class Transfer"
        REPEAT = "REPEAT", "Repeat Class"

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="student_movements",
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="class_movements",
    )

    from_class = models.ForeignKey(
        "academics.SchoolClass",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students_moved_from",
    )

    to_class = models.ForeignKey(
        "academics.SchoolClass",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students_moved_to",
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices,
    )

    session = models.ForeignKey(
        "academics.AcademicSession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    term = models.ForeignKey(
        "academics.AcademicTerm",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    reason = models.TextField(blank=True)

    moved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    moved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-moved_at"]

    def __str__(self):
        return f"{self.student} moved from {self.from_class} to {self.to_class}"