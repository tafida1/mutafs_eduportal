from django import forms



class StudentImportForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            "class": "form-control",
            "accept": ".csv",
        }),
        label="Upload CSV File",
    )



class StaffImportForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            "class": "form-control",
            "accept": ".csv",
        }),
        label="Upload Staff CSV File",
    )



class ParentImportForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            "class": "form-control",
            "accept": ".csv",
        }),
        label="Upload Parent CSV File",
    )


class CBTQuestionImportForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            "class": "form-control",
            "accept": ".csv",
        }),
        label="Upload CBT Questions CSV File",
    )