from django.conf import settings
from django.db import models


class StudentAttendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"
        EXCUSED = "EXCUSED", "Excused"

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="student_attendance_records",
    )

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    school_class = models.ForeignKey(
        "academics.SchoolClass",
        on_delete=models.CASCADE,
        related_name="student_attendance_records",
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

    date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices)
    remarks = models.CharField(max_length=255, blank=True)

    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marked_student_attendance",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_present(self):
        return self.status == self.Status.PRESENT

    @property
    def is_absent(self):
        return self.status == self.Status.ABSENT

    class Meta:
        ordering = ["-date", "student__surname"]
        unique_together = ("school", "student", "date")
        indexes = [
            models.Index(fields=["school", "date"]),
            models.Index(fields=["school", "school_class", "date"]),
            models.Index(fields=["student", "date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"


class StaffAttendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"
        EXCUSED = "EXCUSED", "Excused"

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="staff_attendance_records",
    )

    staff = models.ForeignKey(
        "staffs.StaffProfile",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices)
    remarks = models.CharField(max_length=255, blank=True)

    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marked_staff_attendance",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "staff__user__first_name"]
        unique_together = ("school", "staff", "date")
        indexes = [
            models.Index(fields=["school", "date"]),
            models.Index(fields=["staff", "date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.staff.full_name} - {self.date} - {self.status}"