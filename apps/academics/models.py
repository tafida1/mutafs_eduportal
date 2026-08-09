from django.db import models


class AcademicSession(models.Model):
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="academic_sessions",
    )
    name = models.CharField(max_length=50)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]
        unique_together = ("school", "name")

    def __str__(self):
        return f"{self.name} - {self.school.name}"


class AcademicTerm(models.Model):
    class TermName(models.TextChoices):
        FIRST = "FIRST", "First Term"
        SECOND = "SECOND", "Second Term"
        THIRD = "THIRD", "Third Term"

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="academic_terms",
    )
    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
        related_name="terms",
    )
    name = models.CharField(max_length=20, choices=TermName.choices)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["session", "name"]
        unique_together = ("school", "session", "name")

    def __str__(self):
        return f"{self.get_name_display()} - {self.session.name}"


class SchoolClass(models.Model):
    class Category(models.TextChoices):
        NURSERY = "NURSERY", "Nursery"
        PRIMARY = "PRIMARY", "Primary"
        JSS = "JSS", "Junior Secondary"
        SSS = "SSS", "Senior Secondary"

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="classes",
    )
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=Category.choices)
    position_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position_order", "name"]
        unique_together = ("school", "name")

    def __str__(self):
        return f"{self.name} - {self.school.name}"


class Subject(models.Model):
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="subjects",
    )
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, blank=True)
    category = models.CharField(
        max_length=20,
        choices=SchoolClass.Category.choices,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("school", "name")

    def __str__(self):
        return f"{self.name} - {self.school.name}"