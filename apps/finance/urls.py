from django.urls import path

from . import views

urlpatterns = [

    path("", views.finance_dashboard, name="finance_dashboard"),

    path("categories/", views.fee_category_list, name="fee_category_list"),
    path("categories/create/", views.fee_category_create, name="fee_category_create"),

    path("invoices/", views.invoice_list, name="invoice_list"),

    path(
        "invoices/student/<int:student_id>/generate/",
        views.generate_student_invoice_view,
        name="generate_student_invoice"
    ),

    path(
        "invoices/class/<int:class_id>/bulk-generate/",
        views.bulk_generate_class_invoices,
        name="bulk_generate_class_invoices"
    ),

    path(
        "invoices/<int:pk>/",
        views.invoice_detail,
        name="invoice_detail"
    ),

    path(
        "invoices/<int:invoice_id>/payment/",
        views.record_payment,
        name="record_payment"
    ),

    path(
        "payments/<int:payment_id>/receipt/",
        views.printable_receipt,
        name="printable_receipt"
    ),

    path("student/my-invoices/", views.student_invoice_list, name="student_invoice_list"),
    path("parent/children-invoices/", views.parent_invoice_list, name="parent_invoice_list"),


    path(
        "payments/initialize/<int:invoice_id>/",
        views.initialize_invoice_payment,
        name="initialize_invoice_payment",
    ),

    path(
        "payments/verify/",
        views.verify_payment,
        name="verify_payment",
    ),

    path("structures/", views.fee_structure_list, name="fee_structure_list"),
    path("structures/create/", views.fee_structure_create, name="fee_structure_create"),


    path(
        "transactions/",
        views.payment_transaction_list,
        name="payment_transaction_list",
    ),

    path(
        "my-transactions/",
        views.my_payment_transactions,
        name="my_payment_transactions",
    ),

    path(
        "transactions/<int:transaction_id>/receipt/",
        views.online_payment_receipt,
        name="online_payment_receipt",
    ),
]