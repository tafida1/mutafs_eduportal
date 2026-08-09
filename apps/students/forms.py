from django import forms
from apps.academics.models import SchoolClass, AcademicSession, AcademicTerm
from .models import StudentProfile, StudentClassMovement



class StudentProfileForm(forms.ModelForm):
    temporary_password = forms.CharField(
        required=False,
        min_length=8,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Leave blank to use Passkey@123",
        }),
        help_text="Used for the student's login account.",
    )

    class Meta:
        model = StudentProfile
        fields = [
            "surname",
            "first_name",
            "middle_name",
            "gender",
            "date_of_birth",
            "current_class",
            "passport",
            "guardian_name",
            "guardian_phone",
            "guardian_email",
            "address",
            "status",
            "admission_date",
            "temporary_password",
        ]

        widgets = {
            "surname": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "middle_name": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "current_class": forms.Select(attrs={"class": "form-select"}),
            "passport": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "guardian_name": forms.TextInput(attrs={"class": "form-control"}),
            "guardian_phone": forms.TextInput(attrs={"class": "form-control"}),
            "guardian_email": forms.EmailInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "admission_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)

        if school:
            self.fields["current_class"].queryset = SchoolClass.objects.filter(
                school=school,
                is_active=True,
            )

        if self.instance and self.instance.pk:
            self.fields["temporary_password"].required = False
            self.fields["temporary_password"].help_text = "Leave blank to keep existing password."



class StudentClassMovementForm(forms.Form):
    source_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    destination_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    students = forms.ModelMultipleChoiceField(
        queryset=StudentProfile.objects.none(),
        widget=forms.CheckboxSelectMultiple,
    )

    movement_type = forms.ChoiceField(
        choices=StudentClassMovement.MovementType.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    session = forms.ModelChoiceField(
        queryset=AcademicSession.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False,
    )

    term = forms.ModelChoiceField(
        queryset=AcademicTerm.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False,
    )

    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Reason for movement/promotion/demotion",
        }),
    )

    def __init__(self, *args, **kwargs):
        school = kwargs.pop("school", None)
        super().__init__(*args, **kwargs)

        if school:
            self.fields["source_class"].queryset = SchoolClass.objects.filter(
                school=school,
                is_active=True,
            ).order_by("name")

            self.fields["destination_class"].queryset = SchoolClass.objects.filter(
                school=school,
                is_active=True,
            ).order_by("name")

            self.fields["students"].queryset = StudentProfile.objects.filter(
                school=school,
                status=StudentProfile.Status.ACTIVE,
            ).order_by("surname", "first_name")

            self.fields["session"].queryset = AcademicSession.objects.filter(
                school=school,
            ).order_by("-start_date")

            self.fields["term"].queryset = AcademicTerm.objects.filter(
                school=school,
            )


class SmartPromotionWizardForm(forms.Form):
    source_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    destination_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    session = forms.ModelChoiceField(
        queryset=AcademicSession.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    term = forms.ModelChoiceField(
        queryset=AcademicTerm.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    min_average_for_promotion = forms.DecimalField(
        initial=50,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step": "0.01",
        }),
    )

    max_failed_subjects = forms.IntegerField(
        initial=2,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    reason = forms.CharField(
        required=False,
        initial="End-of-session smart promotion.",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
        }),
    )

    def __init__(self, *args, **kwargs):
        school = kwargs.pop("school", None)
        super().__init__(*args, **kwargs)

        if school:
            self.fields["source_class"].queryset = SchoolClass.objects.filter(
                school=school,
                is_active=True,
            ).order_by("position_order", "name")

            self.fields["destination_class"].queryset = SchoolClass.objects.filter(
                school=school,
                is_active=True,
            ).order_by("position_order", "name")

            self.fields["session"].queryset = AcademicSession.objects.filter(
                school=school,
            ).order_by("-start_date")

            self.fields["term"].queryset = AcademicTerm.objects.filter(
                school=school,
            )