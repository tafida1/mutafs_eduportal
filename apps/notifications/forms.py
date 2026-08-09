from django import forms
from django.utils import timezone

from .models import Announcement


class AnnouncementForm(forms.ModelForm):

    class Meta:
        model = Announcement
        fields = [
            "title",
            "message",
            "audience",
            "priority",
            "attachment",
            "is_pinned",
            "is_active",
            "publish_at",
            "expires_at",
        ]

        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
            }),
            "audience": forms.Select(attrs={"class": "form-select"}),
            "attachment": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "is_pinned": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "publish_at": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local",
            }),
            "expires_at": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local",
            }),
            "priority": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned_data = super().clean()

        publish_at = cleaned_data.get("publish_at")
        expires_at = cleaned_data.get("expires_at")

        if publish_at and expires_at:
            if expires_at <= publish_at:
                raise forms.ValidationError(
                    "Expiry date must be after publish date."
                )

        return cleaned_data