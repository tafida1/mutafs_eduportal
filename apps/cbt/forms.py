from django import forms

from apps.academics.models import AcademicSession, AcademicTerm, SchoolClass, Subject
from .models import CBTQuestion, CBTExam


class CBTQuestionForm(forms.ModelForm):
    class Meta:
        model = CBTQuestion
        fields = [
            "school_class",
            "subject",
            "question_text",
            "diagram",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_option",
            "difficulty",
            "explanation",
            "is_active",
        ]

        widgets = {
            "school_class": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "question_text": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "diagram": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "option_a": forms.TextInput(attrs={"class": "form-control"}),
            "option_b": forms.TextInput(attrs={"class": "form-control"}),
            "option_c": forms.TextInput(attrs={"class": "form-control"}),
            "option_d": forms.TextInput(attrs={"class": "form-control"}),
            "correct_option": forms.Select(attrs={"class": "form-select"}),
            "difficulty": forms.Select(attrs={"class": "form-select"}),
            "explanation": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, school=None, classes=None, subjects=None, **kwargs):
        super().__init__(*args, **kwargs)

        if school:
            self.fields["school_class"].queryset = classes or SchoolClass.objects.filter(
                school=school,
                is_active=True,
            )
            self.fields["subject"].queryset = subjects or Subject.objects.filter(
                school=school,
                is_active=True,
            )


class CBTExamForm(forms.ModelForm):
    class Meta:
        model = CBTExam
        fields = [
            "title",
            "school_class",
            "subject",
            "session",
            "term",
            "questions",
            "duration_minutes",
            "total_questions",
            "pass_mark",
            "start_datetime",
            "end_datetime",
            "shuffle_questions",
            "show_score_immediately",
            "allow_retake",
            "is_active",
        ]

        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "school_class": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "session": forms.Select(attrs={"class": "form-select"}),
            "term": forms.Select(attrs={"class": "form-select"}),
            "questions": forms.SelectMultiple(attrs={"class": "form-select", "size": 10}),
            "duration_minutes": forms.NumberInput(attrs={"class": "form-control"}),
            "total_questions": forms.NumberInput(attrs={"class": "form-control"}),
            "pass_mark": forms.NumberInput(attrs={"class": "form-control"}),
            "start_datetime": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "end_datetime": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "shuffle_questions": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_score_immediately": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "allow_retake": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, school=None, classes=None, subjects=None, **kwargs):
        super().__init__(*args, **kwargs)

        if school:
            class_qs = classes or SchoolClass.objects.filter(school=school, is_active=True)
            subject_qs = subjects or Subject.objects.filter(school=school, is_active=True)

            self.fields["school_class"].queryset = class_qs
            self.fields["subject"].queryset = subject_qs
            self.fields["session"].queryset = AcademicSession.objects.filter(school=school)
            self.fields["term"].queryset = AcademicTerm.objects.filter(school=school)
            self.fields["questions"].queryset = CBTQuestion.objects.filter(
                school=school,
                is_active=True,
            )