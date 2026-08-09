from django import forms

from apps.academics.models import AcademicSession, AcademicTerm, SchoolClass, Subject
from .models import LessonResource


class LessonResourceForm(forms.ModelForm):
    class Meta:
        model = LessonResource
        fields = [
            "title",
            "resource_type",
            "session",
            "term",
            "school_class",
            "subject",
            "description",
            "file",
            "external_link",
            "is_published",
        ]

        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "resource_type": forms.Select(attrs={"class": "form-select"}),
            "session": forms.Select(attrs={"class": "form-select"}),
            "term": forms.Select(attrs={"class": "form-select"}),
            "school_class": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "external_link": forms.URLInput(attrs={"class": "form-control"}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, school=None, classes=None, subjects=None, **kwargs):
        super().__init__(*args, **kwargs)

        if school:
            self.fields["session"].queryset = AcademicSession.objects.filter(school=school)
            self.fields["term"].queryset = AcademicTerm.objects.filter(school=school)
            self.fields["school_class"].queryset = classes or SchoolClass.objects.filter(
                school=school,
                is_active=True,
            )
            self.fields["subject"].queryset = subjects or Subject.objects.filter(
                school=school,
                is_active=True,
            )

    def clean_file(self):
        file = self.cleaned_data.get("file")

        if not file:
            return file

        allowed_extensions = [
            ".pdf", ".doc", ".docx", ".ppt", ".pptx",
            ".txt", ".jpg", ".jpeg", ".png", ".webp",
            ".xlsx", ".csv",
        ]

        filename = file.name.lower()

        if not any(filename.endswith(ext) for ext in allowed_extensions):
            raise forms.ValidationError(
                "Unsupported file type. Upload PDF, Word, PowerPoint, image, Excel, CSV or text file."
            )

        max_size = 15 * 1024 * 1024

        if file.size > max_size:
            raise forms.ValidationError("File size must not exceed 15MB.")

        return file