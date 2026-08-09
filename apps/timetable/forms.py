from django import forms

from apps.academics.models import SchoolClass, Subject
from apps.staffs.models import StaffProfile
from .models import TimeSlot, TimetableEntry


class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = [
            "day",
            "start_time",
            "end_time",
            "label",
            "is_break",
            "is_active",
        ]

        widgets = {
            "day": forms.Select(attrs={"class": "form-select"}),
            "start_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "end_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "label": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Period 1 / Break"}),
            "is_break": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class TimetableEntryForm(forms.ModelForm):
    class Meta:
        model = TimetableEntry
        fields = [
            "school_class",
            "time_slot",
            "subject",
            "teacher",
            "room",
            "note",
            "is_active",
        ]

        widgets = {
            "school_class": forms.Select(attrs={"class": "form-select"}),
            "time_slot": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "teacher": forms.Select(attrs={"class": "form-select"}),
            "room": forms.TextInput(attrs={"class": "form-control"}),
            "note": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)

        if school:
            self.fields["school_class"].queryset = SchoolClass.objects.filter(
                school=school,
                is_active=True,
            )
            self.fields["time_slot"].queryset = TimeSlot.objects.filter(
                school=school,
                is_active=True,
            )
            self.fields["subject"].queryset = Subject.objects.filter(
                school=school,
                is_active=True,
            )
            self.fields["teacher"].queryset = StaffProfile.objects.filter(
                school=school,
                status=StaffProfile.Status.ACTIVE,
                staff_type=StaffProfile.StaffType.TEACHING,
            ).select_related("user")