import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse


class GradeScale(models.Model):
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="grade_scales",
    )
    grade = models.CharField(max_length=5)
    min_score = models.PositiveIntegerField()
    max_score = models.PositiveIntegerField()
    remark = models.CharField(max_length=100)

    class Meta:
        ordering = ["-min_score"]
        unique_together = ("school", "grade")

    def __str__(self):
        return f"{self.grade}: {self.min_score}-{self.max_score}"


class ResultEntry(models.Model):

    class ApprovalStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Needs Correction"

    class PromotionStatus(models.TextChoices):
        PROMOTED = "PROMOTED", "Promoted"
        REPEATED = "REPEATED", "Repeated"
        PROBATION = "PROBATION", "Probation"
        NOT_DECIDED = "NOT_DECIDED", "Not Decided"

    class AcademicRemark(models.TextChoices):
        EXCELLENT = "EXCELLENT", "Excellent Performance"
        VERY_GOOD = "VERY_GOOD", "Very Good Performance"
        GOOD = "GOOD", "Good Performance"
        FAIR = "FAIR", "Fair Performance"
        POOR = "POOR", "Poor Performance"
        CRITICAL = "CRITICAL", "Needs Serious Attention"

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="result_entries",
    )
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="result_entries",
    )
    school_class = models.ForeignKey(
        "academics.SchoolClass",
        on_delete=models.CASCADE,
        related_name="result_entries",
    )
    session = models.ForeignKey(
        "academics.AcademicSession",
        on_delete=models.CASCADE,
        related_name="result_entries",
    )
    term = models.ForeignKey(
        "academics.AcademicTerm",
        on_delete=models.CASCADE,
        related_name="result_entries",
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.CASCADE,
        related_name="result_entries",
    )

    ca_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    exam_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    grade = models.CharField(max_length=5, blank=True)
    remark = models.CharField(max_length=100, blank=True)

    is_published = models.BooleanField(default=False)

    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.DRAFT,
        db_index=True,
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_results",
    )

    approved_at = models.DateTimeField(null=True, blank=True)

    rejection_note = models.TextField(blank=True)

    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entered_results",
    )

    class_position = models.PositiveIntegerField(null=True, blank=True)
    subject_position = models.PositiveIntegerField(null=True, blank=True)

    academic_remark = models.CharField(
        max_length=30,
        choices=AcademicRemark.choices,
        blank=True,
    )

    promotion_status = models.CharField(
        max_length=30,
        choices=PromotionStatus.choices,
        default=PromotionStatus.NOT_DECIDED,
    )

    auto_comment = models.TextField(blank=True)

    principal_comment = models.TextField(blank=True)
    teacher_comment = models.TextField(blank=True)

    verification_token = models.CharField(
        max_length=80,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["student__surname", "subject__name"]
        unique_together = ("school", "student", "session", "term", "subject")
        indexes = [
            models.Index(fields=["school", "session", "term"]),
            models.Index(fields=["student", "session", "term"]),
            models.Index(fields=["school_class", "session", "term"]),
            models.Index(fields=["subject"]),
            models.Index(fields=["is_published"]),
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.name} - {self.total_score}"

    def calculate_total(self):
        self.total_score = self.ca_score + self.exam_score

    def apply_grade(self):
        scale = GradeScale.objects.filter(
            school=self.school,
            min_score__lte=self.total_score,
            max_score__gte=self.total_score,
        ).first()

        if scale:
            self.grade = scale.grade
            self.remark = scale.remark
        else:
            self.grade = ""
            self.remark = ""

    def save(self, *args, **kwargs):
        if not self.verification_token:
            self.verification_token = uuid.uuid4().hex

        self.calculate_total()
        self.apply_grade()
        super().save(*args, **kwargs)
