from django.contrib import admin
from .models import (
    FeeCategory,
    FeeStructure,
    InvoiceItem,
    Payment,
    StudentInvoice,
    PaymentTransaction,
)


admin.site.register(FeeCategory)
admin.site.register(FeeStructure)
admin.site.register(StudentInvoice)
admin.site.register(InvoiceItem)
admin.site.register(Payment)




@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "student",
        "amount",
        "status",
        "payment_method",
        "paid_at",
    )

    list_filter = (
        "status",
        "payment_method",
    )

    search_fields = (
        "reference",
        "student__surname",
        "student__first_name",
    )