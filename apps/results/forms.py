from django import forms
from .models import GradeScale, ResultEntry
from apps.schools.models import School
from apps.students.models import StudentProfile
from apps.academics.models import AcademicSession, AcademicTerm


class GradeScaleForm(forms.ModelForm):
    class Meta:
        model = GradeScale
        fields = ["grade", "min_score", "max_score", "remark"]

        widgets = {
            "grade": forms.TextInput(attrs={"class": "form-control"}),
            "min_score": forms.NumberInput(attrs={"class": "form-control"}),
            "max_score": forms.NumberInput(attrs={"class": "form-control"}),
            "remark": forms.TextInput(attrs={"class": "form-control"}),
        }


class ResultSetupForm(forms.Form):
    session = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    term = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    school_class = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    subject = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, sessions=None, terms=None, classes=None, subjects=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["session"].queryset = sessions
        self.fields["term"].queryset = terms
        self.fields["school_class"].queryset = classes
        self.fields["subject"].queryset = subjects


class ResultEntryForm(forms.ModelForm):
    class Meta:
        model = ResultEntry
        fields = ["ca_score", "exam_score"]

        widgets = {
            "ca_score": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0,
                "max": 30,
                "step": "0.01",
            }),
            "exam_score": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0,
                "max": 70,
                "step": "0.01",
            }),
        }

    def clean_ca_score(self):
        ca = self.cleaned_data["ca_score"]
        if ca < 0 or ca > 30:
            raise forms.ValidationError("CA score must be between 0 and 30.")
        return ca

    def clean_exam_score(self):
        exam = self.cleaned_data["exam_score"]
        if exam < 0 or exam > 70:
            raise forms.ValidationError("Exam score must be between 0 and 70.")
        return exam




class PublicResultCheckForm(forms.Form):
    school = forms.ModelChoiceField(
        queryset=School.objects.filter(is_active=True, result_checker_enabled=True),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    surname = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter surname",
        }),
    )

    passkey = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter result passkey",
        }),
    )

    session = forms.ModelChoiceField(
        queryset=AcademicSession.objects.all().order_by("-start_date"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    term = forms.ModelChoiceField(
        queryset=AcademicTerm.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        school = kwargs.pop("school", None)
        super().__init__(*args, **kwargs)

        if school:
            self.fields["session"].queryset = AcademicSession.objects.filter(
                school=school
            ).order_by("-start_date")

            self.fields["term"].queryset = AcademicTerm.objects.filter(
                school=school
            )