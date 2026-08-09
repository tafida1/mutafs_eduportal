from django import forms
from .models import AcademicSession, AcademicTerm, SchoolClass, Subject


class AcademicSessionForm(forms.ModelForm):
    class Meta:
        model = AcademicSession
        fields = ["name", "start_date", "end_date", "is_current"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "2025/2026"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "is_current": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class AcademicTermForm(forms.ModelForm):
    class Meta:
        model = AcademicTerm
        fields = ["session", "name", "start_date", "end_date", "is_current"]

        widgets = {
            "session": forms.Select(attrs={"class": "form-select"}),
            "name": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "is_current": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)

        if school:
            self.fields["session"].queryset = AcademicSession.objects.filter(school=school)


class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ["name", "category", "position_order", "is_active"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "JSS 1A"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "position_order": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name", "code", "category", "is_active"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Mathematics"}),
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "MTH"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SessionRolloverForm(forms.Form):
    new_session_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Example: 2026/2027",
        }),
    )

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "form-control",
        }),
    )

    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "form-control",
        }),
    )

    confirm_close = forms.BooleanField(
        required=True,
        label="I understand this will close the current session and create a new session.",
    )