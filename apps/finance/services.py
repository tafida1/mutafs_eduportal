from decimal import Decimal
from django.db import models
import requests
from django.conf import settings
from .models import (
    FeeStructure,
    InvoiceItem,
    StudentInvoice,
)


def generate_student_invoice(
    *,
    school,
    student,
    session,
    term,
    generated_by=None,
):
    invoice, created = StudentInvoice.objects.get_or_create(
        school=school,
        student=student,
        session=session,
        term=term,
        defaults={
            "generated_by": generated_by,
        }
    )

    structures = FeeStructure.objects.filter(
        school=school,
        session=session,
        term=term,
        school_class=student.current_class,
        is_active=True,
    ).select_related("category")

    existing_structure_ids = invoice.items.filter(
        fee_structure__isnull=False
    ).values_list("fee_structure_id", flat=True)

    items_to_create = []

    for structure in structures:
        if structure.id not in existing_structure_ids:
            items_to_create.append(
                InvoiceItem(
                    invoice=invoice,
                    fee_structure=structure,
                    category_name=structure.category.name,
                    amount=structure.amount,
                )
            )

    if items_to_create:
        InvoiceItem.objects.bulk_create(items_to_create)

    total = invoice.items.aggregate(
        total=models.Sum("amount")
    )["total"] or Decimal("0.00")

    invoice.total_amount = total
    invoice.balance = total - invoice.amount_paid

    if invoice.balance <= 0:
        invoice.balance = Decimal("0.00")
        invoice.status = StudentInvoice.Status.PAID
    elif invoice.amount_paid > 0:
        invoice.status = StudentInvoice.Status.PARTIAL
    else:
        invoice.status = StudentInvoice.Status.UNPAID

    invoice.save(
        update_fields=[
            "total_amount",
            "balance",
            "status",
        ]
    )

    return invoice



class PaystackService:

    BASE_URL = "https://api.paystack.co"

    @classmethod
    def initialize_payment(
        cls,
        email,
        amount,
        reference,
        callback_url=None,
        metadata=None,
    ):
        url = f"{cls.BASE_URL}/transaction/initialize"

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "email": email,
            "amount": int(amount * 100),
            "reference": reference,
            "callback_url": callback_url or settings.PAYSTACK_CALLBACK_URL,
            "metadata": metadata or {},
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=60,
            )
            return response.json()
        except requests.RequestException as e:
            return {
                "status": False,
                "message": f"Network error connecting to Paystack: {str(e)}",
            }

    @classmethod
    def verify_payment(cls, reference):

        url = f"{cls.BASE_URL}/transaction/verify/{reference}"

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=60,
            )
            return response.json()
        except requests.RequestException as e:
            return {
                "status": False,
                "message": f"Network error connecting to Paystack: {str(e)}",
            }
