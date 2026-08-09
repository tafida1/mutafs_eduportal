from django import forms

from apps.accounts.models import User
from apps.academics.models import SchoolClass, Subject
from .models import StaffProfile


class StaffProfileForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))

    temporary_password = forms.CharField(
        required=False,
        min_length=8,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Leave blank to use Staff@123",
        }),
    )

    class Meta:
        model = StaffProfile
        fields = [
            "staff_type",
            "gender",
            "phone",
            "address",
            "designation",
            "qualification",
            "assigned_classes",
            "assigned_subjects",
            "passport",
            "employment_date",
            "status",
        ]

        widgets = {
            "staff_type": forms.Select(attrs={"class": "form-select"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "designation": forms.TextInput(attrs={"class": "form-control"}),
            "qualification": forms.TextInput(attrs={"class": "form-control"}),
            "assigned_classes": forms.SelectMultiple(attrs={"class": "form-select", "size": 7}),
            "assigned_subjects": forms.SelectMultiple(attrs={"class": "form-select", "size": 7}),
            "passport": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "employment_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school

        if school:
            self.fields["assigned_classes"].queryset = SchoolClass.objects.filter(
                school=school,
                is_active=True,
            )
            self.fields["assigned_subjects"].queryset = Subject.objects.filter(
                school=school,
                is_active=True,
            )

        if self.instance and self.instance.pk:
            user = self.instance.user
            self.fields["username"].initial = user.username
            self.fields["email"].initial = user.email
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["temporary_password"].required = False

    def clean_username(self):
        username = self.cleaned_data["username"]
        qs = User.objects.filter(username=username)

        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.user.pk)

        if qs.exists():
            raise forms.ValidationError("This username is already taken.")

        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if not email:
            return email

        qs = User.objects.filter(email=email)

        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.user.pk)

        if qs.exists():
            raise forms.ValidationError("This email is already in use.")

        return email