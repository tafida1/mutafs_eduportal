from django import forms

from .models import (
    FeeCategory,
    FeeStructure,
    Payment,
)


class FeeCategoryForm(forms.ModelForm):

    class Meta:
        model = FeeCategory
        fields = [
            "name",
            "description",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


class FeeStructureForm(forms.ModelForm):

    class Meta:
        model = FeeStructure
        fields = [
            "session",
            "term",
            "school_class",
            "category",
            "amount",
            "description",
            "is_active",
        ]

        widgets = {
            "session": forms.Select(attrs={"class": "form-select"}),
            "term": forms.Select(attrs={"class": "form-select"}),
            "school_class": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


class PaymentForm(forms.ModelForm):

    class Meta:
        model = Payment
        fields = [
            "amount",
            "payment_method",
            "reference",
            "payment_date",
            "note",
        ]

        widgets = {
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
            }),
            "payment_method": forms.Select(attrs={
                "class": "form-select",
            }),
            "reference": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "payment_date": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local",
            }),
            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),
        }