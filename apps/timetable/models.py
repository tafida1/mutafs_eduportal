from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class TimeSlot(models.Model):
    class Day(models.TextChoices):
        MONDAY = "MONDAY", "Monday"
        TUESDAY = "TUESDAY", "Tuesday"
        WEDNESDAY = "WEDNESDAY", "Wednesday"
        THURSDAY = "THURSDAY", "Thursday"
        FRIDAY = "FRIDAY", "Friday"
        SATURDAY = "SATURDAY", "Saturday"
        SUNDAY = "SUNDAY", "Sunday"

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="time_slots",
    )

    day = models.CharField(max_length=20, choices=Day.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    label = models.CharField(max_length=100, blank=True)

    is_break = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["day", "start_time"]
        unique_together = ("school", "day", "start_time", "end_time")
        indexes = [
            models.Index(fields=["school", "day"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.get_day_display()} {self.start_time} - {self.end_time}"

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")


class TimetableEntry(models.Model):
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="timetable_entries",
    )

    school_class = models.ForeignKey(
        "academics.SchoolClass",
        on_delete=models.CASCADE,
        related_name="timetable_entries",
    )

    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timetable_entries",
    )

    teacher = models.ForeignKey(
        "staffs.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timetable_entries",
    )

    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name="timetable_entries",
    )

    room = models.CharField(max_length=100, blank=True)
    note = models.CharField(max_length=255, blank=True)

    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_timetable_entries",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["time_slot__day", "time_slot__start_time"]
        unique_together = ("school", "school_class", "time_slot")
        indexes = [
            models.Index(fields=["school", "school_class"]),
            models.Index(fields=["teacher"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.school_class.name} - {self.time_slot}"


    def clean(self):
        if not self.school_id:
            return

        if self.teacher and TimetableEntry.objects.filter(
            school_id=self.school_id,
            teacher=self.teacher,
            time_slot=self.time_slot,
            is_active=True,
        ).exclude(pk=self.pk).exists():
            raise ValidationError(
                "This teacher already has another class in this time slot."
            )