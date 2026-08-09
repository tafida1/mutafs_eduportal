from django import forms

from apps.accounts.models import User
from apps.students.models import StudentProfile
from .models import ParentProfile


class ParentProfileForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    temporary_password = forms.CharField(
        required=False,
        min_length=8,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Leave blank to use Parent@123",
        }),
    )

    class Meta:
        model = ParentProfile
        fields = [
            "relationship",
            "phone",
            "alternate_phone",
            "occupation",
            "address",
            "children",
            "is_active",
        ]

        widgets = {
            "relationship": forms.Select(attrs={"class": "form-select"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "alternate_phone": forms.TextInput(attrs={"class": "form-control"}),
            "occupation": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "children": forms.SelectMultiple(attrs={"class": "form-select", "size": 8}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, school=None, **kwargs):
        self.school = school
        super().__init__(*args, **kwargs)

        if school:
            self.fields["children"].queryset = StudentProfile.objects.filter(
                school=school,
            ).select_related("current_class")

        if self.instance and self.instance.pk:
            user = self.instance.user
            self.fields["username"].initial = user.username
            self.fields["email"].initial = user.email
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["temporary_password"].required = False
        else:
            self.fields["children"].required = False

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