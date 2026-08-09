from django import forms


class TeacherAssistantForm(forms.Form):
    TASK_CHOICES = [
        ("LESSON_NOTE", "Generate Lesson Note Outline"),
        ("CBT_QUESTIONS", "Generate CBT Questions"),
        ("EXPLANATION", "Explain Topic Simply"),
        ("ASSIGNMENT", "Generate Assignment Ideas"),
    ]

    task_type = forms.ChoiceField(
        choices=TASK_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Assistant Task",
    )

    subject = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Example: Mathematics",
        }),
        label="Subject",
    )

    school_class = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Example: SSS 1",
        }),
        label="Class",
    )

    topic = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Example: Quadratic Equation",
        }),
        label="Topic",
    )

    extra_instruction = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Optional: Add special instruction...",
        }),
        label="Extra Instruction",
    )