from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.audit.services import log_audit
from apps.core.decorators import role_required
from apps.students.models import StudentProfile
from django.db import IntegrityError
from .forms import (
    FeeCategoryForm,
    FeeStructureForm,
    PaymentForm,
)

from .models import (
    FeeCategory,
    FeeStructure,
    InvoiceItem,
    Payment,
    StudentInvoice,
    PaymentTransaction,
)

from .services import generate_student_invoice
from decimal import Decimal
from django.http import HttpResponse
from django.template.loader import render_to_string
from apps.academics.models import AcademicSession, AcademicTerm, SchoolClass
import uuid
from django.conf import settings
from django.utils import timezone
from .services import PaystackService




def current_school(request):
    return request.user.school


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def finance_dashboard(request):

    school = current_school(request)

    invoices = StudentInvoice.objects.filter(
        school=school
    )

    total_billed = invoices.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    total_paid = invoices.aggregate(
        total=Sum("amount_paid")
    )["total"] or 0

    total_balance = invoices.aggregate(
        total=Sum("balance")
    )["total"] or 0

    return render(request, "finance/dashboard.html", {
        "total_billed": total_billed,
        "total_paid": total_paid,
        "total_balance": total_balance,
        "invoice_count": invoices.count(),
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def fee_category_list(request):

    school = current_school(request)

    categories = FeeCategory.objects.filter(
        school=school
    )

    return render(request, "finance/fee_category_list.html", {
        "categories": categories,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def fee_category_create(request):

    school = current_school(request)

    if request.method == "POST":

        form = FeeCategoryForm(request.POST)

        if form.is_valid():

            category = form.save(commit=False)
            category.school = school
            category.save()

            messages.success(
                request,
                "Fee category created successfully."
            )

            return redirect("fee_category_list")

    else:
        form = FeeCategoryForm()

    return render(request, "finance/form.html", {
        "form": form,
        "title": "Create Fee Category",
        "back_url": "fee_category_list",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def invoice_list(request):

    school = current_school(request)

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    invoices = StudentInvoice.objects.filter(
        school=school
    ).select_related(
        "student",
        "student__user",
        "session",
        "term",
    )

    if query:
        invoices = invoices.filter(
            Q(student__user__first_name__icontains=query)
            | Q(student__user__last_name__icontains=query)
            | Q(student__admission_number__icontains=query)
        )

    if status:
        invoices = invoices.filter(status=status)

    return render(request, "finance/invoice_list.html", {
        "invoices": invoices,
        "query": query,
        "status": status,
        "statuses": StudentInvoice.Status.choices,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def generate_student_invoice_view(request, student_id):

    school = current_school(request)

    student = get_object_or_404(
        StudentProfile,
        pk=student_id,
        school=school,
    )

    current_session = AcademicSession.objects.filter(
        school=school,
        is_current=True,
    ).first()

    current_term = AcademicTerm.objects.filter(
        school=school,
        is_current=True,
    ).first()

    if not current_session or not current_term:

        messages.error(
            request,
            "Current session/term not configured."
        )

        return redirect("invoice_list")

    invoice = generate_student_invoice(
        school=school,
        student=student,
        session=current_session,
        term=current_term,
        generated_by=request.user,
    )

    log_audit(
        request=request,
        school=school,
        action=AuditLog.Action.CREATE,
        module="finance",
        object_type="StudentInvoice",
        object_id=invoice.id,
        description=f"Generated invoice for {student}",
    )

    messages.success(
        request,
        "Invoice generated successfully."
    )

    return redirect("invoice_detail", pk=invoice.pk)



@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def bulk_generate_class_invoices(request, class_id):

    school = current_school(request)

    school_class = get_object_or_404(
        SchoolClass,
        pk=class_id,
        school=school,
    )

    current_session = AcademicSession.objects.filter(
        school=school,
        is_current=True,
    ).first()

    current_term = AcademicTerm.objects.filter(
        school=school,
        is_current=True,
    ).first()

    students = StudentProfile.objects.filter(
        school=school,
        current_class=school_class,
        is_active=True,
    )

    count = 0

    for student in students:

        generate_student_invoice(
            school=school,
            student=student,
            session=current_session,
            term=current_term,
            generated_by=request.user,
        )

        count += 1

    messages.success(
        request,
        f"{count} invoices generated successfully."
    )

    return redirect("invoice_list")


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        StudentInvoice.objects.select_related(
            "school",
            "student",
            "student__user",
            "session",
            "term",
        ),
        pk=pk,
    )

    user = request.user

    if user.role == User.Role.SCHOOL_ADMIN:
        if invoice.school != user.school:
            messages.error(request, "You cannot access this invoice.")
            return redirect("dashboard_router")

    elif user.role == User.Role.STUDENT:
        if invoice.student.user != user:
            messages.error(request, "You cannot access this invoice.")
            return redirect("dashboard_router")

    elif user.role == User.Role.PARENT:
        parent = getattr(user, "parent_profile", None)

        if not parent or not parent.children.filter(pk=invoice.student.pk).exists():
            messages.error(request, "You cannot access this invoice.")
            return redirect("dashboard_router")

    else:
        messages.error(request, "You cannot access this invoice.")
        return redirect("dashboard_router")

    items = invoice.items.all()
    payments = invoice.payments.all()

    return render(request, "finance/invoice_detail.html", {
        "invoice": invoice,
        "items": items,
        "payments": payments,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def record_payment(request, invoice_id):

    school = current_school(request)

    invoice = get_object_or_404(
        StudentInvoice,
        pk=invoice_id,
        school=school,
    )

    if request.method == "POST":

        form = PaymentForm(request.POST)

        if form.is_valid():

            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.received_by = request.user
            payment.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.CREATE,
                module="finance",
                object_type="Payment",
                object_id=payment.id,
                description=f"Recorded payment for invoice #{invoice.id}",
            )

            messages.success(
                request,
                "Payment recorded successfully."
            )

            return redirect("invoice_detail", pk=invoice.pk)

    else:
        form = PaymentForm(
            initial={
                "amount": invoice.balance
            }
        )

    return render(request, "finance/form.html", {
        "form": form,
        "title": "Record Payment",
        "back_url": "invoice_list",
    })


@login_required
def printable_receipt(request, payment_id):

    payment = get_object_or_404(
        Payment.objects.select_related(
            "invoice",
            "invoice__student",
            "invoice__student__user",
        ),
        pk=payment_id,
    )

    user = request.user

    if user.role == User.Role.SCHOOL_ADMIN:
        if payment.invoice.school != user.school:
            return redirect("dashboard")

    html = render_to_string(
        "finance/receipt_print.html",
        {
            "payment": payment,
        }
    )

    return HttpResponse(html)



@login_required
@role_required(User.Role.STUDENT)
def student_invoice_list(request):
    school = current_school(request)

    student = get_object_or_404(
        StudentProfile,
        user=request.user,
        school=school,
    )

    invoices = StudentInvoice.objects.filter(
        school=school,
        student=student,
    ).select_related("session", "term")

    return render(request, "finance/student_invoice_list.html", {
        "student": student,
        "invoices": invoices,
    })


@login_required
@role_required(User.Role.PARENT)
def parent_invoice_list(request):
    school = current_school(request)

    parent = get_object_or_404(
        request.user.parent_profile.__class__,
        user=request.user,
        school=school,
    )

    children = parent.children.all()

    invoices = StudentInvoice.objects.filter(
        school=school,
        student__in=children,
    ).select_related(
        "student",
        "session",
        "term",
    )

    return render(request, "finance/parent_invoice_list.html", {
        "parent": parent,
        "children": children,
        "invoices": invoices,
    })




@login_required
@role_required(
    User.Role.PARENT,
    User.Role.STUDENT,
    User.Role.SCHOOL_ADMIN,
)
def initialize_invoice_payment(request, invoice_id):

    invoice = get_object_or_404(
        StudentInvoice,
        pk=invoice_id,
    )

    if invoice.balance <= 0:
        messages.warning(request, "Invoice already settled.")
        return redirect("invoice_detail", pk=invoice.id)

    email = request.user.email

    if not email:
        messages.error(request, "Your account email is missing.")
        return redirect("invoice_detail", pk=invoice.id)

    reference = f"MUTAFS-{uuid.uuid4().hex[:12].upper()}"

    transaction = PaymentTransaction.objects.create(
        school=invoice.school,
        invoice=invoice,
        student=invoice.student,
        reference=reference,
        amount=invoice.balance,
        status=PaymentTransaction.Status.PENDING,
    )

    response = PaystackService.initialize_payment(
        email=email,
        amount=invoice.balance,
        reference=reference,
        metadata={
            "invoice_id": invoice.id,
            "student_id": invoice.student.id,
            "school_id": invoice.school.id,
        },
    )

    if response.get("status") is True:
        payment_url = response["data"]["authorization_url"]
        return redirect(payment_url)

    transaction.status = PaymentTransaction.Status.FAILED
    transaction.gateway_response = str(response)
    transaction.save()

    error_message = response.get("message", "Unable to initialize payment.")

    messages.error(
        request,
        f"Unable to initialize payment: {error_message}"
    )

    return redirect("invoice_detail", pk=invoice.id)



@login_required
def verify_payment(request):

    reference = request.GET.get("reference")

    if not reference:
        messages.error(request, "Invalid payment reference.")
        return redirect("dashboard")

    transaction = get_object_or_404(
        PaymentTransaction,
        reference=reference,
    )

    response = PaystackService.verify_payment(reference)

    if response.get("status") is not True:
        transaction.status = PaymentTransaction.Status.FAILED
        transaction.gateway_response = str(response)
        transaction.save()

        messages.error(request, "Payment verification failed.")
        return redirect("dashboard")

    data = response.get("data", {})

    if data.get("status") != "success":
        transaction.status = PaymentTransaction.Status.FAILED
        transaction.gateway_response = str(response)
        transaction.save()

        messages.error(request, "Payment not successful.")
        return redirect("dashboard")

    transaction.status = PaymentTransaction.Status.SUCCESS
    transaction.gateway_response = str(response)
    transaction.paid_at = timezone.now()
    transaction.save()

    invoice = transaction.invoice

    if invoice:
        Payment.objects.create(
            invoice=invoice,
            amount=transaction.amount,
            payment_method=Payment.Method.ONLINE,
            reference=transaction.reference,
            payment_date=transaction.paid_at,
            received_by=request.user,
            note="Online payment via Paystack",
        )

    messages.success(request, "Payment successful.")

    return redirect("online_payment_receipt", transaction_id=transaction.id)


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def fee_structure_list(request):
    school = current_school(request)

    structures = FeeStructure.objects.filter(
        school=school
    ).select_related(
        "session",
        "term",
        "school_class",
        "category",
    )

    return render(request, "finance/fee_structure_list.html", {
        "structures": structures,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def fee_structure_create(request):
    school = current_school(request)

    if request.method == "POST":
        form = FeeStructureForm(request.POST)

        form.fields["session"].queryset = AcademicSession.objects.filter(school=school)
        form.fields["term"].queryset = AcademicTerm.objects.filter(school=school)
        form.fields["school_class"].queryset = SchoolClass.objects.filter(school=school)
        form.fields["category"].queryset = FeeCategory.objects.filter(
            school=school,
            is_active=True,
        )

        if form.is_valid():
            structure = form.save(commit=False)
            structure.school = school
            structure.created_by = request.user
        try:
            structure.save()

            messages.success(
                request,
                "Fee structure created successfully."
            )

            return redirect("fee_structure_list")

        except IntegrityError:
            messages.error(
                request,
                "This fee structure already exists."
            )
            return redirect("fee_structure_list")
    else:
        form = FeeStructureForm()

        form.fields["session"].queryset = AcademicSession.objects.filter(school=school)
        form.fields["term"].queryset = AcademicTerm.objects.filter(school=school)
        form.fields["school_class"].queryset = SchoolClass.objects.filter(school=school)
        form.fields["category"].queryset = FeeCategory.objects.filter(
            school=school,
            is_active=True,
        )

    return render(request, "finance/form.html", {
        "form": form,
        "title": "Create Fee Structure",
        "back_url": "fee_structure_list",
    })




@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def payment_transaction_list(request):
    school = current_school(request)

    transactions = PaymentTransaction.objects.filter(
        school=school,
    ).select_related(
        "student",
        "student__user",
        "invoice",
    ).order_by("-created_at")

    return render(request, "finance/payment_transactions.html", {
        "transactions": transactions,
    })


@login_required
def my_payment_transactions(request):
    user = request.user

    if user.role == User.Role.STUDENT:
        student = get_object_or_404(
            StudentProfile,
            user=user,
            school=user.school,
        )

        transactions = PaymentTransaction.objects.filter(
            student=student,
        )

    elif user.role == User.Role.PARENT:
        parent = getattr(user, "parent_profile", None)

        if not parent:
            messages.error(request, "Parent profile not found.")
            return redirect("dashboard_router")

        transactions = PaymentTransaction.objects.filter(
            student__in=parent.children.all(),
        )

    else:
        messages.error(request, "You cannot access this page.")
        return redirect("dashboard_router")

    return render(request, "finance/my_payment_transactions.html", {
        "transactions": transactions.select_related(
            "student",
            "student__user",
            "invoice",
        ).order_by("-created_at")
    })


@login_required
def online_payment_receipt(request, transaction_id):
    transaction = get_object_or_404(
        PaymentTransaction.objects.select_related(
            "school",
            "student",
            "student__user",
            "invoice",
        ),
        pk=transaction_id,
    )

    user = request.user

    if user.role == User.Role.SCHOOL_ADMIN:
        if transaction.school != user.school:
            messages.error(request, "You cannot access this receipt.")
            return redirect("dashboard_router")

    elif user.role == User.Role.STUDENT:
        if transaction.student.user != user:
            messages.error(request, "You cannot access this receipt.")
            return redirect("dashboard_router")

    elif user.role == User.Role.PARENT:
        parent = getattr(user, "parent_profile", None)

        if not parent or not parent.children.filter(pk=transaction.student.pk).exists():
            messages.error(request, "You cannot access this receipt.")
            return redirect("dashboard_router")

    else:
        messages.error(request, "You cannot access this receipt.")
        return redirect("dashboard_router")

    return render(request, "finance/online_payment_receipt.html", {
        "transaction": transaction,
    })