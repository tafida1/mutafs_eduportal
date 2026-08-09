from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from apps.accounts.models import User


class ProfileUpdateForm(forms.ModelForm):

    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "profile_picture",
        ]

        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "last_name": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control"
            }),

            "phone_number": forms.TextInput(attrs={
                "class": "form-control"
            }),
        }


class StyledPasswordChangeForm(PasswordChangeForm):

    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control"
        })
    )

    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control"
        })
    )

    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control"
        })
    )