from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.audit.services import log_audit
from apps.core.decorators import role_required
from .forms import ParentProfileForm
from .models import ParentProfile




def get_user_school(request):
    return request.user.school


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def parent_list(request):
    school = get_user_school(request)
    query = request.GET.get("q", "").strip()
    active = request.GET.get("active", "").strip()

    parents = ParentProfile.objects.filter(
        school=school,
    ).select_related("user").prefetch_related("children")

    if query:
        parents = parents.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__email__icontains=query)
            | Q(phone__icontains=query)
            | Q(children__surname__icontains=query)
            | Q(children__first_name__icontains=query)
            | Q(children__admission_number__icontains=query)
        ).distinct()

    if active == "active":
        parents = parents.filter(is_active=True)

    if active == "inactive":
        parents = parents.filter(is_active=False)

    return render(request, "parents/parent_list.html", {
        "parents": parents,
        "query": query,
        "active": active,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
@transaction.atomic
def parent_create(request):
    school = get_user_school(request)

    if request.method == "POST":
        form = ParentProfileForm(request.POST, school=school)

        if form.is_valid():
            password = form.cleaned_data.get("temporary_password") or "Parent@123"

            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data.get("email") or f'{form.cleaned_data["username"]}@parents.mutafs.local',
                password=password,
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                role=User.Role.PARENT,
                school=school,
                must_change_password=True,
                is_active=form.cleaned_data["is_active"],
            )

            parent = form.save(commit=False)
            parent.user = user
            parent.school = school
            parent.save()
            form.save_m2m()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.CREATE,
                module="parents",
                object_type="ParentProfile",
                object_id=parent.id,
                description=f"Created parent/guardian {parent.full_name}",
            )

            messages.success(request, "Parent/Guardian account created successfully.")
            return redirect("parent_detail", pk=parent.pk)
    else:
        form = ParentProfileForm(school=school)

    return render(request, "parents/parent_form.html", {
        "form": form,
        "title": "Create Parent/Guardian",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def parent_detail(request, pk):
    school = get_user_school(request)

    parent = get_object_or_404(
        ParentProfile.objects.select_related("user", "school").prefetch_related(
            "children",
            "children__current_class",
        ),
        pk=pk,
        school=school,
    )

    audit_logs = school.audit_logs.filter(
        object_type="ParentProfile",
        object_id=str(parent.id),
    )[:10]

    return render(request, "parents/parent_detail.html", {
        "parent": parent,
        "audit_logs": audit_logs,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
@transaction.atomic
def parent_update(request, pk):
    school = get_user_school(request)
    parent = get_object_or_404(ParentProfile, pk=pk, school=school)

    if request.method == "POST":
        form = ParentProfileForm(request.POST, instance=parent, school=school)

        if form.is_valid():
            parent = form.save(commit=False)

            user = parent.user
            user.username = form.cleaned_data["username"]
            user.email = form.cleaned_data.get("email") or user.email
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.is_active = form.cleaned_data["is_active"]

            password = form.cleaned_data.get("temporary_password")
            if password:
                user.set_password(password)
                user.must_change_password = True

            user.save()
            parent.save()
            form.save_m2m()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.UPDATE,
                module="parents",
                object_type="ParentProfile",
                object_id=parent.id,
                description=f"Updated parent/guardian {parent.full_name}",
            )

            messages.success(request, "Parent/Guardian updated successfully.")
            return redirect("parent_detail", pk=parent.pk)
    else:
        form = ParentProfileForm(instance=parent, school=school)

    return render(request, "parents/parent_form.html", {
        "form": form,
        "title": "Edit Parent/Guardian",
        "parent": parent,
    })


@login_required
@role_required(User.Role.PARENT)
def parent_portal_dashboard(request):
    from django.db.models import Avg, Sum
    from apps.attendance.models import StudentAttendance
    from apps.cbt.models import CBTAttempt
    from apps.finance.models import StudentInvoice
    from apps.notifications.models import UserNotification
    from apps.results.models import ResultEntry
    from apps.timetable.models import TimetableEntry
    from datetime import datetime

    school = request.user.school

    parent = get_object_or_404(
        ParentProfile.objects.prefetch_related(
            "children",
            "children__user",
            "children__current_class",
        ),
        user=request.user,
        school=school,
    )

    children = parent.children.all()

    total_children = children.count()

    invoices = StudentInvoice.objects.filter(
        school=school,
        student__in=children,
    )

    total_fees_balance = invoices.aggregate(
        total=Sum("balance")
    )["total"] or 0

    result_average = ResultEntry.objects.filter(
        school=school,
        student__in=children,
        is_published=True,
    ).aggregate(
        avg=Avg("total_score")
    )["avg"] or 0

    cbt_average = CBTAttempt.objects.filter(
        school=school,
        student__in=children,
        status=CBTAttempt.Status.SUBMITTED,
    ).aggregate(
        avg=Avg("percentage")
    )["avg"] or 0

    attendance_records = StudentAttendance.objects.filter(
        school=school,
        student__in=children,
    )

    total_attendance = attendance_records.count()

    present_attendance = attendance_records.filter(
        status=StudentAttendance.Status.PRESENT,
    ).count()

    attendance_percentage = 0

    if total_attendance > 0:
        attendance_percentage = round(
            (present_attendance / total_attendance) * 100,
            1,
        )

    recent_notifications = UserNotification.objects.filter(
        user=request.user,
        announcement__is_active=True,
    ).select_related(
        "announcement",
    ).order_by("-created_at")[:5]

    today_day = datetime.now().strftime("%A").upper()

    today_timetable = TimetableEntry.objects.filter(
        school=school,
        school_class__in=children.values_list("current_class", flat=True),
        time_slot__day=today_day,
        is_active=True,
    ).select_related(
        "subject",
        "school_class",
        "time_slot",
    ).order_by("time_slot__start_time")[:8]

    child_cards = []

    for child in children:
        child_attendance = StudentAttendance.objects.filter(
            school=school,
            student=child,
        )

        child_total_attendance = child_attendance.count()

        child_present = child_attendance.filter(
            status=StudentAttendance.Status.PRESENT,
        ).count()

        child_attendance_percentage = 0

        if child_total_attendance > 0:
            child_attendance_percentage = round(
                (child_present / child_total_attendance) * 100,
                1,
            )

        child_fee_balance = StudentInvoice.objects.filter(
            school=school,
            student=child,
        ).aggregate(
            total=Sum("balance")
        )["total"] or 0

        child_result_average = ResultEntry.objects.filter(
            school=school,
            student=child,
            is_published=True,
        ).aggregate(
            avg=Avg("total_score")
        )["avg"] or 0

        child_cards.append({
            "child": child,
            "attendance_percentage": child_attendance_percentage,
            "fee_balance": child_fee_balance,
            "result_average": child_result_average,
        })

    context = {
        "parent": parent,
        "children": children,
        "child_cards": child_cards,
        "total_children": total_children,
        "total_fees_balance": total_fees_balance,
        "result_average": round(result_average, 1),
        "cbt_average": round(cbt_average, 1),
        "attendance_percentage": attendance_percentage,
        "recent_notifications": recent_notifications,
        "today_timetable": today_timetable,
    }

    return render(request, "parents/portal_dashboard.html", context)

    