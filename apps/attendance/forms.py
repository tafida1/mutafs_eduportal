from django import forms
from .models import StudentAttendance, StaffAttendance


class AttendanceDateClassForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )

    school_class = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, classes=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["school_class"].queryset = classes


class StaffAttendanceDateForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )


class StudentAttendanceFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Search student name or admission number...",
        }),
    )

    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    status = forms.ChoiceField(
        required=False,
        choices=[("", "All Statuses")] + list(StudentAttendance.Status.choices),
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class StaffAttendanceFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Search staff name or staff ID...",
        }),
    )

    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    status = forms.ChoiceField(
        required=False,
        choices=[("", "All Statuses")] + list(StaffAttendance.Status.choices),
        widget=forms.Select(attrs={"class": "form-select"}),
    )