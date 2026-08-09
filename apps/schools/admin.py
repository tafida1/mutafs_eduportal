from django.contrib import admin
from .models import School, SubscriptionPlan, SchoolSubscription, SubscriptionPayment




@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "portal_subpath",
        "subscription_status",
        "subscription_end_date",
        "is_active",
        "is_verified",
        "created_at",
    )
    list_filter = (
        "subscription_status",
        "is_active",
        "is_verified",
        "result_checker_enabled",
        "cbt_enabled",
        "finance_enabled",
        "parent_portal_enabled",
    )
    search_fields = (
        "name",
        "code",
        "portal_subpath",
        "email",
        "phone",
    )
    prepopulated_fields = {
        "slug": ("name",),
        "portal_subpath": ("name",),
    }
    readonly_fields = ("created_at", "updated_at")



@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "billing_cycle",
        "price",
        "max_students",
        "max_staff",
        "is_active",
    )

    list_filter = (
        "billing_cycle",
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )


@admin.register(SchoolSubscription)
class SchoolSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "school",
        "plan",
        "status",
        "start_date",
        "end_date",
        "auto_disable_on_expiry",
    )
    list_filter = ("status", "plan", "auto_disable_on_expiry")
    search_fields = ("school__name",)


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "subscription",
        "amount",
        "payment_method",
        "reference",
        "payment_date",
        "received_by",
    )
    list_filter = ("payment_method", "payment_date")
    search_fields = ("subscription__school__name", "reference")