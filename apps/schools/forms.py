from django import forms
from apps.accounts.models import User
from .models import School, SubscriptionPlan, SchoolSubscription, SubscriptionPayment



class SchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = [
            "name",
            "portal_subpath",
            "code",
            "email",
            "phone",
            "address",
            "logo",
            "result_stamp",
            "is_active",
            "is_verified",
            "subscription_status",
            "subscription_start_date",
            "subscription_end_date",
            "result_checker_enabled",
            "cbt_enabled",
            "finance_enabled",
            "parent_portal_enabled",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "portal_subpath": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "logo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "result_stamp": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "subscription_status": forms.Select(attrs={"class": "form-select"}),
            "subscription_start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "subscription_end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_verified": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "result_checker_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "cbt_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "finance_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "parent_portal_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SchoolAdminUserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        min_length=8,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "password",
            "is_active",
        ]

        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def save(self, commit=True, school=None):
        user = super().save(commit=False)
        user.role = User.Role.SCHOOL_ADMIN
        user.school = school
        user.is_staff = False
        user.is_superuser = False
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user



class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "name",
            "description",
            "billing_cycle",
            "price",
            "max_students",
            "max_staff",
            "cbt_enabled",
            "finance_enabled",
            "parent_portal_enabled",
            "result_checker_enabled",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "billing_cycle": forms.Select(attrs={"class": "form-select"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "max_students": forms.NumberInput(attrs={"class": "form-control"}),
            "max_staff": forms.NumberInput(attrs={"class": "form-control"}),
            "cbt_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "finance_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "parent_portal_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "result_checker_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SchoolSubscriptionForm(forms.ModelForm):
    class Meta:
        model = SchoolSubscription
        fields = [
            "plan",
            "status",
            "start_date",
            "end_date",
            "auto_disable_on_expiry",
            "notes",
        ]

        widgets = {
            "plan": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "auto_disable_on_expiry": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class SubscriptionPaymentForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPayment
        fields = [
            "amount",
            "payment_method",
            "reference",
            "payment_date",
            "note",
        ]

        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "reference": forms.TextInput(attrs={"class": "form-control"}),
            "payment_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "name",
            "description",
            "billing_cycle",
            "price",
            "max_students",
            "max_staff",
            "cbt_enabled",
            "finance_enabled",
            "parent_portal_enabled",
            "result_checker_enabled",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),
            "billing_cycle": forms.Select(attrs={"class": "form-select"}),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
            }),
            "max_students": forms.NumberInput(attrs={"class": "form-control"}),
            "max_staff": forms.NumberInput(attrs={"class": "form-control"}),

            "cbt_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "finance_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "parent_portal_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "result_checker_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SchoolBrandingForm(forms.ModelForm):
    class Meta:
        model = School
        fields = [
            "logo",
            "primary_color",
            "secondary_color",
            "accent_color",
        ]

        widgets = {
            "primary_color": forms.TextInput(attrs={
                "class": "form-control",
                "type": "color",
            }),
            "secondary_color": forms.TextInput(attrs={
                "class": "form-control",
                "type": "color",
            }),
            "accent_color": forms.TextInput(attrs={
                "class": "form-control",
                "type": "color",
            }),
        }


class TenantControlForm(forms.ModelForm):
    class Meta:
        model = School
        fields = [
            "custom_domain",
            "subdomain",
            "is_active",
            "maintenance_mode",
            "maintenance_message",
            "result_checker_enabled",
            "cbt_enabled",
            "finance_enabled",
            "parent_portal_enabled",
            "allow_custom_branding",
            "storage_limit_mb",
        ]

        widgets = {
            "custom_domain": forms.TextInput(attrs={"class": "form-control"}),
            "subdomain": forms.TextInput(attrs={"class": "form-control"}),
            "maintenance_message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),
            "storage_limit_mb": forms.NumberInput(attrs={"class": "form-control"}),

            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "maintenance_mode": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "result_checker_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "cbt_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "finance_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "parent_portal_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "allow_custom_branding": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }