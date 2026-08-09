from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class FeeCategory(models.Model):

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="fee_categories",
    )

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("school", "name")

    def __str__(self):
        return self.name


class FeeStructure(models.Model):

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="fee_structures",
    )

    session = models.ForeignKey(
        "academics.AcademicSession",
        on_delete=models.CASCADE,
        related_name="fee_structures",
    )

    term = models.ForeignKey(
        "academics.AcademicTerm",
        on_delete=models.CASCADE,
        related_name="fee_structures",
    )

    school_class = models.ForeignKey(
        "academics.SchoolClass",
        on_delete=models.CASCADE,
        related_name="fee_structures",
    )

    category = models.ForeignKey(
        FeeCategory,
        on_delete=models.CASCADE,
        related_name="fee_structures",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_fee_structures",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["school_class__name"]
        unique_together = (
            "school",
            "session",
            "term",
            "school_class",
            "category",
        )

    def __str__(self):
        return f"{self.school_class.name} - {self.category.name}"


class StudentInvoice(models.Model):

    class Status(models.TextChoices):
        UNPAID = "UNPAID", "Unpaid"
        PARTIAL = "PARTIAL", "Partial"
        PAID = "PAID", "Paid"

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="student_invoices",
    )

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="invoices",
    )

    session = models.ForeignKey(
        "academics.AcademicSession",
        on_delete=models.CASCADE,
    )

    term = models.ForeignKey(
        "academics.AcademicTerm",
        on_delete=models.CASCADE,
    )

    generated_at = models.DateTimeField(auto_now_add=True)

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UNPAID,
    )

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return f"Invoice - {self.student}"

    def recalculate(self):

        total_paid = self.payments.aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0.00")

        self.amount_paid = total_paid
        self.balance = self.total_amount - total_paid

        if self.balance <= 0:
            self.status = self.Status.PAID
        elif total_paid > 0:
            self.status = self.Status.PARTIAL
        else:
            self.status = self.Status.UNPAID

        self.save(
            update_fields=[
                "amount_paid",
                "balance",
                "status",
            ]
        )

        from apps.core.cache_utils import clear_school_cache
        clear_school_cache(self.school_id)


class InvoiceItem(models.Model):

    invoice = models.ForeignKey(
        StudentInvoice,
        on_delete=models.CASCADE,
        related_name="items",
    )

    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    category_name = models.CharField(max_length=150)

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        ordering = ["category_name"]

    def __str__(self):
        return self.category_name


class Payment(models.Model):

    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        TRANSFER = "TRANSFER", "Bank Transfer"
        POS = "POS", "POS"
        ONLINE = "ONLINE", "Online"

    invoice = models.ForeignKey(
        StudentInvoice,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    payment_method = models.CharField(
        max_length=20,
        choices=Method.choices,
    )

    reference = models.CharField(
        max_length=255,
        blank=True,
    )

    payment_date = models.DateTimeField(
        default=timezone.now,
    )

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date"]

    def __str__(self):
        return f"{self.invoice.student} - {self.amount}"

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        self.invoice.recalculate()

        from apps.core.cache_utils import clear_school_cache
        clear_school_cache(self.invoice.school_id)


class PaymentTransaction(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="payment_transactions",
    )

    invoice = models.ForeignKey(
        "finance.StudentInvoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="payment_transactions",
    )

    reference = models.CharField(
        max_length=120,
        unique=True,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    payment_method = models.CharField(
        max_length=50,
        default="PAYSTACK",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    gateway_response = models.TextField(
        blank=True,
        null=True,
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.reference} - {self.status}"
