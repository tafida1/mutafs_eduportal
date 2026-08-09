from django.conf import settings
from django.db import models
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField
from ckeditor.fields import RichTextField


class CBTQuestion(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "EASY", "Easy"
        MEDIUM = "MEDIUM", "Medium"
        HARD = "HARD", "Hard"

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="cbt_questions",
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.CASCADE,
        related_name="cbt_questions",
    )
    school_class = models.ForeignKey(
        "academics.SchoolClass",
        on_delete=models.CASCADE,
        related_name="cbt_questions",
    )

    question_text = RichTextUploadingField(
        help_text="Supports maths, science symbols, diagrams, images, tables and formatted text."
    )

    option_a = RichTextField()
    option_b = RichTextField()
    option_c = RichTextField()
    option_d = RichTextField()

    diagram = models.ImageField(
        upload_to="cbt_diagrams/",
        blank=True,
        null=True,
        help_text="Optional diagram, graph, equation image or science illustration."
    )

    question_image = models.ImageField(
        upload_to="cbt/questions/",
        blank=True,
        null=True,
    )

    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ("EASY", "Easy"),
            ("MEDIUM", "Medium"),
            ("HARD", "Hard"),
        ],
        default="MEDIUM",
    )

    estimated_time = models.PositiveIntegerField(
        default=60,
        help_text="Estimated seconds",
    )

    is_calculation = models.BooleanField(default=False)

    correct_option = models.CharField(
        max_length=1,
        choices=[
            ("A", "A"),
            ("B", "B"),
            ("C", "C"),
            ("D", "D"),
        ],
    )

    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM,
    )

    explanation = RichTextUploadingField(blank=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_cbt_questions",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school", "school_class", "subject"]),
            models.Index(fields=["difficulty"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.subject.name} - {self.question_text[:50]}"


class CBTExam(models.Model):
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="cbt_exams",
    )

    title = models.CharField(max_length=255)

    school_class = models.ForeignKey(
        "academics.SchoolClass",
        on_delete=models.CASCADE,
        related_name="cbt_exams",
    )

    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.CASCADE,
        related_name="cbt_exams",
    )

    session = models.ForeignKey(
        "academics.AcademicSession",
        on_delete=models.CASCADE,
        related_name="cbt_exams",
    )

    term = models.ForeignKey(
        "academics.AcademicTerm",
        on_delete=models.CASCADE,
        related_name="cbt_exams",
    )

    questions = models.ManyToManyField(
        CBTQuestion,
        related_name="exams",
        blank=True,
    )

    duration_minutes = models.PositiveIntegerField(default=30)
    total_questions = models.PositiveIntegerField(default=20)
    pass_mark = models.PositiveIntegerField(default=50)

    start_datetime = models.DateTimeField(null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)

    shuffle_questions = models.BooleanField(default=True)
    show_score_immediately = models.BooleanField(default=True)
    allow_retake = models.BooleanField(default=False)

    is_active = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_cbt_exams",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school", "school_class", "subject"]),
            models.Index(fields=["session", "term"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.title

    def is_available(self):
        now = timezone.now()

        if not self.is_active:
            return False

        if self.start_datetime and now < self.start_datetime:
            return False

        if self.end_datetime and now > self.end_datetime:
            return False

        return True


class CBTAttempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        SUBMITTED = "SUBMITTED", "Submitted"

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="cbt_attempts",
    )

    exam = models.ForeignKey(
        CBTExam,
        on_delete=models.CASCADE,
        related_name="attempts",
    )

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="cbt_attempts",
    )

    questions = models.ManyToManyField(
        CBTQuestion,
        through="CBTAttemptQuestion",
        related_name="attempts",
    )

    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )

    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["school", "exam"]),
            models.Index(fields=["student", "exam"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.exam.title}"

    @property
    def passed(self):
        return self.percentage >= self.exam.pass_mark


class CBTAttemptQuestion(models.Model):
    attempt = models.ForeignKey(
        CBTAttempt,
        on_delete=models.CASCADE,
        related_name="attempt_questions",
    )

    question = models.ForeignKey(
        CBTQuestion,
        on_delete=models.CASCADE,
        related_name="attempt_question_records",
    )

    selected_option = models.CharField(
        max_length=1,
        choices=[
            ("", "Not Answered"),
            ("A", "A"),
            ("B", "B"),
            ("C", "C"),
            ("D", "D"),
        ],
        blank=True,
        default="",
    )

    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ("attempt", "question")

    def __str__(self):
        return f"{self.attempt} - {self.question.id}"