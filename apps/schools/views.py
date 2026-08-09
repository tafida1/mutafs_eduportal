import csv, uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.audit.services import log_audit
from apps.core.decorators import role_required
from .forms import SchoolForm, SchoolAdminUserForm, SubscriptionPlanForm, SchoolSubscriptionForm, SubscriptionPaymentForm, SchoolBrandingForm, TenantControlForm
from .models import School, SubscriptionPlan, SchoolSubscription, SubscriptionPayment
from django.utils import timezone
from decimal import Decimal
from django.conf import settings
from apps.finance.services import PaystackService
from apps.students.models import StudentProfile
from apps.staffs.models import StaffProfile





@login_required
@role_required(User.Role.SUPER_ADMIN)
def school_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    active = request.GET.get("active", "").strip()

    schools = School.objects.all().annotate(
        total_users=Count("users", distinct=True)
    )

    if query:
        schools = schools.filter(
            Q(name__icontains=query)
            | Q(code__icontains=query)
            | Q(portal_subpath__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
        )

    if status:
        schools = schools.filter(subscription_status=status)

    if active == "active":
        schools = schools.filter(is_active=True)

    if active == "inactive":
        schools = schools.filter(is_active=False)

    context = {
        "schools": schools,
        "query": query,
        "status": status,
        "active": active,
        "subscription_statuses": School.SubscriptionStatus.choices,
    }

    return render(request, "schools/school_list.html", context)


@login_required
@role_required(User.Role.SUPER_ADMIN)
def school_create(request):
    if request.method == "POST":
        form = SchoolForm(request.POST, request.FILES)

        if form.is_valid():
            school = form.save()

            log_audit(
                request=request,
                action=AuditLog.Action.CREATE,
                module="schools",
                object_type="School",
                object_id=school.id,
                description=f"Created school: {school.name}",
            )

            messages.success(request, "School created successfully.")
            return redirect("school_detail", pk=school.pk)
    else:
        form = SchoolForm()

    return render(request, "schools/school_form.html", {
        "form": form,
        "title": "Create School",
    })


@login_required
@role_required(User.Role.SUPER_ADMIN)
def school_detail(request, pk):
    school = get_object_or_404(School, pk=pk)

    school_admins = User.objects.filter(
        school=school,
        role=User.Role.SCHOOL_ADMIN,
    ).order_by("first_name", "last_name", "username")

    audit_logs = school.audit_logs.select_related("actor").all()[:20]

    context = {
        "school": school,
        "school_admins": school_admins,
        "audit_logs": audit_logs,
    }

    return render(request, "schools/school_detail.html", context)


@login_required
@role_required(User.Role.SUPER_ADMIN)
def school_update(request, pk):
    school = get_object_or_404(School, pk=pk)

    if request.method == "POST":
        form = SchoolForm(request.POST, request.FILES, instance=school)

        if form.is_valid():
            school = form.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.UPDATE,
                module="schools",
                object_type="School",
                object_id=school.id,
                description=f"Updated school: {school.name}",
            )

            messages.success(request, "School updated successfully.")
            return redirect("school_detail", pk=school.pk)
    else:
        form = SchoolForm(instance=school)

    return render(request, "schools/school_form.html", {
        "form": form,
        "school": school,
        "title": "Edit School",
    })


@login_required
@role_required(User.Role.SUPER_ADMIN)
def school_toggle_status(request, pk):
    school = get_object_or_404(School, pk=pk)

    school.is_active = not school.is_active
    school.save(update_fields=["is_active", "updated_at"])

    action = (
        AuditLog.Action.SCHOOL_ENABLED
        if school.is_active
        else AuditLog.Action.SCHOOL_DISABLED
    )

    log_audit(
        request=request,
        school=school,
        action=action,
        module="schools",
        object_type="School",
        object_id=school.id,
        description=f"{'Enabled' if school.is_active else 'Disabled'} school: {school.name}",
    )

    messages.success(
        request,
        f"{school.name} has been {'enabled' if school.is_active else 'disabled'}."
    )

    return redirect("school_detail", pk=school.pk)


@login_required
@role_required(User.Role.SUPER_ADMIN)
def school_create_admin(request, pk):
    school = get_object_or_404(School, pk=pk)

    if request.method == "POST":
        form = SchoolAdminUserForm(request.POST)

        if form.is_valid():
            user = form.save(school=school)

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.CREATE,
                module="accounts",
                object_type="User",
                object_id=user.id,
                description=f"Created school admin {user.username} for {school.name}",
            )

            messages.success(request, "School Admin created successfully.")
            return redirect("school_detail", pk=school.pk)
    else:
        form = SchoolAdminUserForm()

    return render(request, "schools/school_admin_form.html", {
        "form": form,
        "school": school,
    })


@login_required
@role_required(User.Role.SUPER_ADMIN)
def school_export_csv(request):
    schools = School.objects.all().order_by("name")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="mutafs_schools.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Name",
        "Code",
        "Portal Subpath",
        "Email",
        "Phone",
        "Subscription Status",
        "Subscription End Date",
        "Active",
        "Verified",
        "Created At",
    ])

    for school in schools:
        writer.writerow([
            school.name,
            school.code,
            school.portal_subpath,
            school.email,
            school.phone,
            school.subscription_status,
            school.subscription_end_date,
            "Yes" if school.is_active else "No",
            "Yes" if school.is_verified else "No",
            school.created_at,
        ])

    log_audit(
        request=request,
        action=AuditLog.Action.EXPORT,
        module="schools",
        description="Exported schools CSV report.",
    )

    return response



@login_required
@role_required(User.Role.SUPER_ADMIN)
def subscription_dashboard(request):
    subscriptions = SchoolSubscription.objects.select_related("school", "plan")

    today = timezone.localdate()

    context = {
        "total_subscriptions": subscriptions.count(),
        "active_subscriptions": subscriptions.filter(status=SchoolSubscription.Status.ACTIVE).count(),
        "trial_subscriptions": subscriptions.filter(status=SchoolSubscription.Status.TRIAL).count(),
        "expired_subscriptions": subscriptions.filter(status=SchoolSubscription.Status.EXPIRED).count(),
        "expiring_soon": subscriptions.filter(
            end_date__isnull=False,
            end_date__gte=today,
            end_date__lte=today + timezone.timedelta(days=14),
        ).count(),
        "total_revenue": SubscriptionPayment.objects.aggregate(total=Sum("amount"))["total"] or 0,
        "recent_subscriptions": subscriptions.order_by("end_date")[:10],
    }

    return render(request, "schools/subscriptions/dashboard.html", context)


@login_required
@role_required(User.Role.SUPER_ADMIN)
def subscription_plan_list(request):
    plans = SubscriptionPlan.objects.all()

    return render(request, "schools/subscriptions/plan_list.html", {
        "plans": plans,
    })


@login_required
@role_required(User.Role.SUPER_ADMIN)
def subscription_plan_create(request):
    if request.method == "POST":
        form = SubscriptionPlanForm(request.POST)

        if form.is_valid():
            plan = form.save()

            log_audit(
                request=request,
                action=AuditLog.Action.CREATE,
                module="subscriptions",
                object_type="SubscriptionPlan",
                object_id=plan.id,
                description=f"Created subscription plan {plan.name}",
            )

            messages.success(request, "Subscription plan created successfully.")
            return redirect("subscription_plan_list")
    else:
        form = SubscriptionPlanForm()

    return render(request, "schools/subscriptions/form.html", {
        "form": form,
        "title": "Create Subscription Plan",
        "back_url": "subscription_plan_list",
    })


@login_required
@role_required(User.Role.SUPER_ADMIN)
def subscription_plan_update(request, pk):
    plan = get_object_or_404(SubscriptionPlan, pk=pk)

    if request.method == "POST":
        form = SubscriptionPlanForm(request.POST, instance=plan)

        if form.is_valid():
            plan = form.save()

            log_audit(
                request=request,
                action=AuditLog.Action.UPDATE,
                module="subscriptions",
                object_type="SubscriptionPlan",
                object_id=plan.id,
                description=f"Updated subscription plan {plan.name}",
            )

            messages.success(request, "Subscription plan updated successfully.")
            return redirect("subscription_plan_list")
    else:
        form = SubscriptionPlanForm(instance=plan)

    return render(request, "schools/subscriptions/form.html", {
        "form": form,
        "title": "Edit Subscription Plan",
        "back_url": "subscription_plan_list",
    })


@login_required
@role_required(User.Role.SUPER_ADMIN)
def school_subscription_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    subscriptions = SchoolSubscription.objects.select_related("school", "plan")

    if query:
        subscriptions = subscriptions.filter(school__name__icontains=query)

    if status:
        subscriptions = subscriptions.filter(status=status)

    return render(request, "schools/subscriptions/subscription_list.html", {
        "subscriptions": subscriptions,
        "query": query,
        "status": status,
        "statuses": SchoolSubscription.Status.choices,
    })


@login_required
@role_required(User.Role.SUPER_ADMIN)
def school_subscription_update(request, school_id):
    school = get_object_or_404(School, pk=school_id)

    subscription, created = SchoolSubscription.objects.get_or_create(
        school=school,
        defaults={
            "status": SchoolSubscription.Status.TRIAL,
            "start_date": timezone.localdate(),
            "updated_by": request.user,
        },
    )

    if request.method == "POST":
        form = SchoolSubscriptionForm(request.POST, instance=subscription)

        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.updated_by = request.user
            subscription.save()
            subscription.sync_school_status()

            if subscription.plan:
                school.cbt_enabled = subscription.plan.cbt_enabled
                school.finance_enabled = subscription.plan.finance_enabled
                school.parent_portal_enabled = subscription.plan.parent_portal_enabled
                school.result_checker_enabled = subscription.plan.result_checker_enabled
                school.save(update_fields=[
                    "cbt_enabled",
                    "finance_enabled",
                    "parent_portal_enabled",
                    "result_checker_enabled",
                    "updated_at",
                ])

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.UPDATE,
                module="subscriptions",
                object_type="SchoolSubscription",
                object_id=subscription.id,
                description=f"Updated subscription for {school.name}",
            )

            messages.success(request, "School subscription updated successfully.")
            return redirect("school_subscription_list")
    else:
        form = SchoolSubscriptionForm(instance=subscription)

    return render(request, "schools/subscriptions/form.html", {
        "form": form,
        "title": f"Update Subscription — {school.name}",
        "back_url": "school_subscription_list",
    })


@login_required
@role_required(User.Role.SUPER_ADMIN)
def subscription_payment_create(request, subscription_id):
    subscription = get_object_or_404(
        SchoolSubscription.objects.select_related("school", "plan"),
        pk=subscription_id,
    )

    if request.method == "POST":
        form = SubscriptionPaymentForm(request.POST)

        if form.is_valid():
            payment = form.save(commit=False)
            payment.subscription = subscription
            payment.received_by = request.user
            payment.save()

            log_audit(
                request=request,
                school=subscription.school,
                action=AuditLog.Action.CREATE,
                module="subscriptions",
                object_type="SubscriptionPayment",
                object_id=payment.id,
                description=f"Recorded subscription payment for {subscription.school.name}",
            )

            messages.success(request, "Subscription payment recorded successfully.")
            return redirect("school_subscription_list")
    else:
        initial_amount = subscription.plan.price if subscription.plan else 0
        form = SubscriptionPaymentForm(initial={"amount": initial_amount})

    return render(request, "schools/subscriptions/form.html", {
        "form": form,
        "title": f"Record Payment — {subscription.school.name}",
        "back_url": "school_subscription_list",
    })


@login_required
@role_required(User.Role.SUPER_ADMIN)
def sync_expired_subscriptions(request):
    subscriptions = SchoolSubscription.objects.select_related("school")

    count = 0

    for subscription in subscriptions:
        old_status = subscription.status
        subscription.sync_school_status()

        if subscription.status != old_status:
            count += 1

    messages.success(request, f"{count} subscription records synced.")
    return redirect("subscription_dashboard")



@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def subscription_dashboard(request):
    school = request.user.school

    subscription = SchoolSubscription.objects.filter(
        school=school,
    ).select_related(
        "plan",
    ).first()

    payments = SubscriptionPayment.objects.filter(
        subscription__school=school,
    ).select_related(
        "subscription",
        "subscription__plan",
    ).order_by("-created_at")

    plans = SubscriptionPlan.objects.filter(
        is_active=True,
    ).order_by(
        "price",
        "name",
    )

    return render(request, "schools/subscription_dashboard.html", {
        "school": school,
        "subscription": subscription,
        "payments": payments,
        "plans": plans,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def initialize_subscription_payment(request):
    school = request.user.school

    plan_id = request.GET.get("plan")

    plan = get_object_or_404(
        SubscriptionPlan,
        pk=plan_id,
        is_active=True,
    )

    if not request.user.email:
        messages.error(request, "Your account email is required before payment.")
        return redirect("subscription_dashboard")

    reference = f"SUB-{uuid.uuid4().hex[:12].upper()}"

    subscription, created = SchoolSubscription.objects.get_or_create(
        school=school,
        defaults={
            "plan": plan,
            "status": SchoolSubscription.Status.TRIAL,
            "start_date": timezone.localdate(),
            "end_date": timezone.localdate(),
        },
    )

    subscription.plan = plan
    subscription.save(update_fields=["plan", "updated_at"])

    payment = SubscriptionPayment.objects.create(
        subscription=subscription,
        amount=plan.price,
        payment_method=SubscriptionPayment.Method.ONLINE,
        reference=reference,
        received_by=request.user,
        note=f"{plan.name} subscription payment via Paystack",
    )

    callback_url = request.build_absolute_uri(
        f"/schools/subscription/verify/?reference={reference}"
    )

    response = PaystackService.initialize_payment(
        email=request.user.email,
        amount=plan.price,
        reference=reference,
        callback_url=callback_url,
        metadata={
            "subscription_id": subscription.id,
            "school_id": school.id,
            "plan_id": plan.id,
            "payment_id": payment.id,
        },
    )

    if response.get("status") is True:
        return redirect(response["data"]["authorization_url"])

    messages.error(
        request,
        response.get("message", "Unable to initialize subscription payment."),
    )

    return redirect("subscription_dashboard")


@login_required
def verify_subscription_payment(request):
    reference = request.GET.get("reference")

    if not reference:
        messages.error(request, "Invalid payment reference.")
        return redirect("subscription_dashboard")

    payment = get_object_or_404(
        SubscriptionPayment.objects.select_related(
            "subscription",
            "subscription__school",
            "subscription__plan",
        ),
        reference=reference,
    )

    response = PaystackService.verify_payment(reference)

    if response.get("status") is not True:
        messages.error(
            request,
            response.get("message", "Payment verification failed."),
        )
        return redirect("subscription_dashboard")

    data = response.get("data", {})

    if data.get("status") != "success":
        messages.error(request, "Payment was not successful.")
        return redirect("subscription_dashboard")

    subscription = payment.subscription
    school = subscription.school
    plan = subscription.plan

    if not plan:
        messages.error(request, "Subscription plan not found.")
        return redirect("subscription_dashboard")

    start_date = timezone.localdate()

    if school.subscription_end_date and school.subscription_end_date > start_date:
        start_date = school.subscription_end_date

    if plan.billing_cycle == SubscriptionPlan.BillingCycle.MONTHLY:
        duration_days = 30
    elif plan.billing_cycle == SubscriptionPlan.BillingCycle.TERMLY:
        duration_days = 90
    elif plan.billing_cycle == SubscriptionPlan.BillingCycle.YEARLY:
        duration_days = 365
    else:
        duration_days = 30

    end_date = start_date + timezone.timedelta(days=duration_days)

    subscription.status = SchoolSubscription.Status.ACTIVE
    subscription.start_date = start_date
    subscription.end_date = end_date
    subscription.save(update_fields=[
        "status",
        "start_date",
        "end_date",
        "updated_at",
    ])

    school.subscription_status = School.SubscriptionStatus.ACTIVE
    school.subscription_start_date = start_date
    school.subscription_end_date = end_date
    school.is_active = True
    school.save(update_fields=[
        "subscription_status",
        "subscription_start_date",
        "subscription_end_date",
        "is_active",
        "updated_at",
    ])

    payment.note = f"{payment.note}\nVerified successfully via Paystack."
    payment.save(update_fields=["note"])

    messages.success(request, "Subscription payment successful.")

    return redirect("subscription_dashboard")



@login_required
@role_required(User.Role.SUPER_ADMIN)
def subscription_plan_list(request):
    plans = SubscriptionPlan.objects.all().order_by("price", "name")

    return render(request, "schools/subscription_plan_list.html", {
        "plans": plans,
    })


@login_required
@role_required(User.Role.SUPER_ADMIN)
def subscription_plan_create(request):
    if request.method == "POST":
        form = SubscriptionPlanForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Subscription plan created successfully.")
            return redirect("subscription_plan_list")
    else:
        form = SubscriptionPlanForm()

    return render(request, "schools/subscription_plan_form.html", {
        "form": form,
        "title": "Create Subscription Plan",
    })


@login_required
@role_required(User.Role.SUPER_ADMIN)
def subscription_plan_update(request, pk):
    plan = get_object_or_404(SubscriptionPlan, pk=pk)

    if request.method == "POST":
        form = SubscriptionPlanForm(request.POST, instance=plan)

        if form.is_valid():
            form.save()
            messages.success(request, "Subscription plan updated successfully.")
            return redirect("subscription_plan_list")
    else:
        form = SubscriptionPlanForm(instance=plan)

    return render(request, "schools/subscription_plan_form.html", {
        "form": form,
        "title": "Update Subscription Plan",
        "plan": plan,
    })


@login_required
@role_required(User.Role.SUPER_ADMIN)
def subscription_plan_toggle(request, pk):
    plan = get_object_or_404(SubscriptionPlan, pk=pk)

    plan.is_active = not plan.is_active
    plan.save(update_fields=["is_active"])

    if plan.is_active:
        messages.success(request, "Subscription plan activated.")
    else:
        messages.warning(request, "Subscription plan disabled.")

    return redirect("subscription_plan_list")


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def school_branding_settings(request):
    school = request.user.school

    if not school.allow_custom_branding:
        messages.error(request, "Custom branding is not enabled for your school plan.")
        return redirect("school_admin_dashboard")

    if request.method == "POST":
        form = SchoolBrandingForm(
            request.POST,
            request.FILES,
            instance=school,
        )

        if form.is_valid():
            form.save()
            messages.success(request, "School branding updated successfully.")
            return redirect("school_branding_settings")
    else:
        form = SchoolBrandingForm(instance=school)

    return render(request, "schools/branding_settings.html", {
        "form": form,
        "school": school,
    })


@login_required
@role_required(User.Role.SUPER_ADMIN)
def tenant_control_center(request):
    schools = School.objects.annotate(
        students_count=Count("students", distinct=True),
        staff_count=Count("staff_members", distinct=True),
    ).select_related(
        "subscription",
    ).order_by("name")

    return render(request, "schools/tenant_control_center.html", {
        "schools": schools,
    })

@login_required
@role_required(User.Role.SUPER_ADMIN)
def tenant_control_update(request, school_id):
    school = get_object_or_404(School, pk=school_id)

    if request.method == "POST":
        form = TenantControlForm(request.POST, instance=school)

        if form.is_valid():
            form.save()
            messages.success(request, "Tenant settings updated successfully.")
            return redirect("tenant_control_center")
    else:
        form = TenantControlForm(instance=school)

    students_count = StudentProfile.objects.filter(school=school).count()
    staff_count = StaffProfile.objects.filter(school=school).count()

    return render(request, "schools/tenant_control_form.html", {
        "form": form,
        "school": school,
        "students_count": students_count,
        "staff_count": staff_count,
    })