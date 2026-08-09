from django import forms

from apps.accounts.models import User
from .models import Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["body", "attachment"]

        widgets = {
            "body": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Type your message...",
            }),
        }


class StartConversationForm(forms.Form):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Recipient",
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 4,
            "placeholder": "Write your message...",
        }),
        label="Message",
    )

    attachment = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if not user:
            return

        qs = User.objects.exclude(id=user.id)

        if user.is_super_admin:
            qs = qs.filter(role=User.Role.SCHOOL_ADMIN)

        elif user.is_school_admin:
            qs = qs.filter(
                school=user.school,
                role__in=[
                    User.Role.TEACHER,
                    User.Role.STUDENT,
                    User.Role.PARENT,
                ],
            )

        elif user.is_teacher:
            qs = qs.filter(
                school=user.school,
                role__in=[
                    User.Role.SCHOOL_ADMIN,
                    User.Role.STUDENT,
                    User.Role.PARENT,
                ],
            )

        elif user.is_parent:
            qs = qs.filter(
                school=user.school,
                role__in=[
                    User.Role.SCHOOL_ADMIN,
                    User.Role.TEACHER,
                ],
            )

        elif user.is_student:
            qs = qs.filter(
                school=user.school,
                role__in=[
                    User.Role.SCHOOL_ADMIN,
                    User.Role.TEACHER,
                ],
            )

        else:
            qs = User.objects.none()

        self.fields["recipient"].queryset = qs.order_by(
            "role",
            "first_name",
            "last_name",
            "username",
        )