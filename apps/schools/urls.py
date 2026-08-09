from django.urls import path
from . import views

urlpatterns = [
    path("", views.school_list, name="school_list"),
    path("create/", views.school_create, name="school_create"),
    path("export/csv/", views.school_export_csv, name="school_export_csv"),
    path("<int:pk>/", views.school_detail, name="school_detail"),
    path("<int:pk>/edit/", views.school_update, name="school_update"),
    path("<int:pk>/toggle-status/", views.school_toggle_status, name="school_toggle_status"),
    path("<int:pk>/create-admin/", views.school_create_admin, name="school_create_admin"),


    path("subscriptions/", views.subscription_dashboard, name="subscription_dashboard"),

    path("subscriptions/plans/", views.subscription_plan_list, name="subscription_plan_list"),
    path("subscriptions/plans/create/", views.subscription_plan_create, name="subscription_plan_create"),
    path("subscriptions/plans/<int:pk>/edit/", views.subscription_plan_update, name="subscription_plan_update"),

    path("subscriptions/schools/", views.school_subscription_list, name="school_subscription_list"),
    path("subscriptions/schools/<int:school_id>/edit/", views.school_subscription_update, name="school_subscription_update"),

    path("subscriptions/payments/<int:subscription_id>/create/", views.subscription_payment_create, name="subscription_payment_create"),

    path("subscriptions/sync-expired/", views.sync_expired_subscriptions, name="sync_expired_subscriptions"),

    
    path(
        "subscription/",
        views.subscription_dashboard,
        name="subscription_dashboard",
    ),

    path(
        "subscription/pay/",
        views.initialize_subscription_payment,
        name="initialize_subscription_payment",
    ),

    path(
        "subscription/verify/",
        views.verify_subscription_payment,
        name="verify_subscription_payment",
    ),


    path(
        "subscription-plans/",
        views.subscription_plan_list,
        name="subscription_plan_list",
    ),

    path(
        "subscription-plans/create/",
        views.subscription_plan_create,
        name="subscription_plan_create",
    ),

    path(
        "subscription-plans/<int:pk>/edit/",
        views.subscription_plan_update,
        name="subscription_plan_update",
    ),

    path(
        "subscription-plans/<int:pk>/toggle/",
        views.subscription_plan_toggle,
        name="subscription_plan_toggle",
    ),


    path(
        "branding/",
        views.school_branding_settings,
        name="school_branding_settings",
    ),

    path(
        "tenants/",
        views.tenant_control_center,
        name="tenant_control_center",
    ),

    path(
        "tenants/<int:school_id>/edit/",
        views.tenant_control_update,
        name="tenant_control_update",
    ),
]