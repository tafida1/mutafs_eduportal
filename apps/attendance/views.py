import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Avg, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from apps.accounts.models import User
from apps.academics.models import AcademicSession, AcademicTerm, SchoolClass
from apps.audit.models import AuditLog
from apps.audit.services import log_audit
from apps.core.decorators import role_required
from apps.staffs.models import StaffProfile
from apps.students.models import StudentProfile
from .forms import AttendanceDateClassForm, StaffAttendanceDateForm
from .models import StudentAttendance, StaffAttendance


def get_user_school(request):
    return request.user.school


def teacher_allowed_classes(request):
    try:
        staff = request.user.staff_profile
        return staff.assigned_classes.filter(school=request.user.school, is_active=True)
    except StaffProfile.DoesNotExist:
        return SchoolClass.objects.none()


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def attendance_dashboard(request):
    school = get_user_school(request)
    today = timezone.localdate()

    if request.user.is_teacher:
        classes = teacher_allowed_classes(request)
    else:
        classes = SchoolClass.objects.filter(school=school, is_active=True)

    chronic_absentees = StudentAttendance.objects.filter(
        school=school,
        status=StudentAttendance.Status.ABSENT,
    ).values(
        "student__surname",
        "student__first_name",
    ).annotate(
        absent_count=Count("id")
    ).order_by("-absent_count")[:10]

    context = {
        "today": today,
        "classes_count": classes.count(),
        "student_present_today": StudentAttendance.objects.filter(
            school=school,
            date=today,
            status=StudentAttendance.Status.PRESENT,
        ).count(),
        "student_absent_today": StudentAttendance.objects.filter(
            school=school,
            date=today,
            status=StudentAttendance.Status.ABSENT,
        ).count(),
        "staff_present_today": StaffAttendance.objects.filter(
            school=school,
            date=today,
            status=StaffAttendance.Status.PRESENT,
        ).count(),
        "staff_absent_today": StaffAttendance.objects.filter(
            school=school,
            date=today,
            status=StaffAttendance.Status.ABSENT,
        ).count(),
        "chronic_absentees": chronic_absentees,
    }

    return render(request, "attendance/dashboard.html", context)


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def student_attendance_select(request):
    school = get_user_school(request)

    if request.user.is_teacher:
        classes = teacher_allowed_classes(request)
    else:
        classes = SchoolClass.objects.filter(school=school, is_active=True)

    if request.method == "POST":
        form = AttendanceDateClassForm(request.POST, classes=classes)

        if form.is_valid():
            date = form.cleaned_data["date"]
            school_class = form.cleaned_data["school_class"]

            return redirect(
                "student_attendance_mark",
                class_id=school_class.id,
                date=date.isoformat(),
            )
    else:
        form = AttendanceDateClassForm(
            classes=classes,
            initial={"date": timezone.localdate()},
        )

    return render(request, "attendance/student_attendance_select.html", {
        "form": form,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
@transaction.atomic
def student_attendance_mark(request, class_id, date):
    school = get_user_school(request)

    if request.user.is_teacher:
        school_class = get_object_or_404(
            teacher_allowed_classes(request),
            pk=class_id,
        )
    else:
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
        status=StudentProfile.Status.ACTIVE,
    ).order_by("surname", "first_name")

    existing_records = StudentAttendance.objects.filter(
        school=school,
        school_class=school_class,
        date=date,
    )

    existing_map = {
        record.student_id: record
        for record in existing_records
    }

    if request.method == "POST":
        for student in students:
            status = request.POST.get(f"status_{student.id}")
            remarks = request.POST.get(f"remarks_{student.id}", "").strip()

            if not status:
                continue

            StudentAttendance.objects.update_or_create(
                school=school,
                student=student,
                date=date,
                defaults={
                    "school_class": school_class,
                    "session": current_session,
                    "term": current_term,
                    "status": status,
                    "remarks": remarks,
                    "marked_by": request.user,
                },
            )

        log_audit(
            request=request,
            school=school,
            action=AuditLog.Action.UPDATE,
            module="attendance",
            object_type="StudentAttendance",
            object_id=school_class.id,
            description=f"Marked student attendance for {school_class.name} on {date}",
        )

        messages.success(request, "Student attendance saved successfully.")
        return redirect("student_attendance_report")

    return render(request, "attendance/student_attendance_mark.html", {
        "school_class": school_class,
        "students": students,
        "date": date,
        "statuses": StudentAttendance.Status.choices,
        "existing_map": existing_map,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def student_attendance_report(request):
    school = get_user_school(request)

    query = request.GET.get("q", "").strip()
    date = request.GET.get("date", "").strip()
    status = request.GET.get("status", "").strip()
    class_id = request.GET.get("class", "").strip()

    records = StudentAttendance.objects.filter(
        school=school,
    ).select_related("student", "school_class", "marked_by")

    if request.user.is_teacher:
        allowed_classes = teacher_allowed_classes(request)
        records = records.filter(school_class__in=allowed_classes)
        classes = allowed_classes
    else:
        classes = SchoolClass.objects.filter(school=school, is_active=True)

    if query:
        records = records.filter(
            Q(student__surname__icontains=query)
            | Q(student__first_name__icontains=query)
            | Q(student__admission_number__icontains=query)
        )

    if date:
        records = records.filter(date=date)

    if status:
        records = records.filter(status=status)

    if class_id:
        records = records.filter(school_class_id=class_id)

    return render(request, "attendance/student_attendance_report.html", {
        "records": records,
        "query": query,
        "date": date,
        "status": status,
        "class_id": class_id,
        "classes": classes,
        "statuses": StudentAttendance.Status.choices,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def staff_attendance_select(request):
    if request.method == "POST":
        form = StaffAttendanceDateForm(request.POST)

        if form.is_valid():
            date = form.cleaned_data["date"]
            return redirect("staff_attendance_mark", date=date.isoformat())
    else:
        form = StaffAttendanceDateForm(initial={"date": timezone.localdate()})

    return render(request, "attendance/staff_attendance_select.html", {
        "form": form,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
@transaction.atomic
def staff_attendance_mark(request, date):
    school = get_user_school(request)

    staffs = StaffProfile.objects.filter(
        school=school,
        status=StaffProfile.Status.ACTIVE,
    ).select_related("user").order_by("user__first_name", "user__last_name")

    existing_records = StaffAttendance.objects.filter(
        school=school,
        date=date,
    )

    existing_map = {
        record.staff_id: record
        for record in existing_records
    }

    if request.method == "POST":
        for staff in staffs:
            status = request.POST.get(f"status_{staff.id}")
            remarks = request.POST.get(f"remarks_{staff.id}", "").strip()

            if not status:
                continue

            StaffAttendance.objects.update_or_create(
                school=school,
                staff=staff,
                date=date,
                defaults={
                    "status": status,
                    "remarks": remarks,
                    "marked_by": request.user,
                },
            )

        log_audit(
            request=request,
            school=school,
            action=AuditLog.Action.UPDATE,
            module="attendance",
            object_type="StaffAttendance",
            description=f"Marked staff attendance on {date}",
        )

        messages.success(request, "Staff attendance saved successfully.")
        return redirect("staff_attendance_report")

    return render(request, "attendance/staff_attendance_mark.html", {
        "staffs": staffs,
        "date": date,
        "statuses": StaffAttendance.Status.choices,
        "existing_map": existing_map,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def staff_attendance_report(request):
    school = get_user_school(request)

    query = request.GET.get("q", "").strip()
    date = request.GET.get("date", "").strip()
    status = request.GET.get("status", "").strip()

    records = StaffAttendance.objects.filter(
        school=school,
    ).select_related("staff", "staff__user", "marked_by")

    if query:
        records = records.filter(
            Q(staff__staff_id__icontains=query)
            | Q(staff__user__first_name__icontains=query)
            | Q(staff__user__last_name__icontains=query)
            | Q(staff__phone__icontains=query)
        )

    if date:
        records = records.filter(date=date)

    if status:
        records = records.filter(status=status)

    return render(request, "attendance/staff_attendance_report.html", {
        "records": records,
        "query": query,
        "date": date,
        "status": status,
        "statuses": StaffAttendance.Status.choices,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def student_attendance_export_csv(request):
    school = get_user_school(request)

    records = StudentAttendance.objects.filter(
        school=school,
    ).select_related("student", "school_class", "marked_by")

    if request.user.is_teacher:
        records = records.filter(school_class__in=teacher_allowed_classes(request))

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="student_attendance.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Date",
        "Student",
        "Admission Number",
        "Class",
        "Status",
        "Remarks",
        "Marked By",
    ])

    for record in records:
        writer.writerow([
            record.date,
            record.student.full_name,
            record.student.admission_number,
            record.school_class.name,
            record.get_status_display(),
            record.remarks,
            record.marked_by.username if record.marked_by else "",
        ])

    log_audit(
        request=request,
        school=school,
        action=AuditLog.Action.EXPORT,
        module="attendance",
        description="Exported student attendance CSV.",
    )

    return response


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def staff_attendance_export_csv(request):
    school = get_user_school(request)

    records = StaffAttendance.objects.filter(
        school=school,
    ).select_related("staff", "staff__user", "marked_by")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="staff_attendance.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Date",
        "Staff",
        "Staff ID",
        "Status",
        "Remarks",
        "Marked By",
    ])

    for record in records:
        writer.writerow([
            record.date,
            record.staff.full_name,
            record.staff.staff_id,
            record.get_status_display(),
            record.remarks,
            record.marked_by.username if record.marked_by else "",
        ])

    log_audit(
        request=request,
        school=school,
        action=AuditLog.Action.EXPORT,
        module="attendance",
        description="Exported staff attendance CSV.",
    )

    return response


@login_required
@role_required(User.Role.STUDENT)
def student_attendance_portal(request):

    school = request.user.school

    student = get_object_or_404(
        StudentProfile.objects.select_related(
            "user",
            "current_class",
        ),
        user=request.user,
        school=school,
    )

    attendance_records = StudentAttendance.objects.filter(
        school=school,
        student=student,
    ).select_related(
        "school_class",
    ).order_by("-date")

    total_days = attendance_records.count()

    present_days = attendance_records.filter(
        status=StudentAttendance.Status.PRESENT
    ).count()

    absent_days = attendance_records.filter(
        status=StudentAttendance.Status.ABSENT
    ).count()

    late_days = attendance_records.filter(
        status=StudentAttendance.Status.LATE
    ).count()

    attendance_percentage = 0

    if total_days > 0:
        attendance_percentage = round(
            (present_days / total_days) * 100,
            1
        )

    monthly_stats = attendance_records.values(
        "date__month"
    ).annotate(
        present=Count(
            "id",
            filter=Q(status=StudentAttendance.Status.PRESENT)
        ),
        absent=Count(
            "id",
            filter=Q(status=StudentAttendance.Status.ABSENT)
        ),
        late=Count(
            "id",
            filter=Q(status=StudentAttendance.Status.LATE)
        ),
    ).order_by("date__month")

    return render(request, "attendance/student_portal.html", {
        "student": student,
        "attendance_records": attendance_records,
        "total_days": total_days,
        "present_days": present_days,
        "absent_days": absent_days,
        "late_days": late_days,
        "attendance_percentage": attendance_percentage,
        "monthly_stats": monthly_stats,
    })


@login_required
@role_required(User.Role.PARENT)
def parent_attendance_portal(request):

    school = request.user.school

    parent = getattr(request.user, "parent_profile", None)

    if not parent:
        messages.error(request, "Parent profile not found.")
        return redirect("dashboard_router")

    children = parent.children.select_related(
        "user",
        "current_class",
    )

    attendance_records = StudentAttendance.objects.filter(
        school=school,
        student__in=children,
    ).select_related(
        "student",
        "school_class",
    ).order_by("-date")

    return render(request, "attendance/parent_portal.html", {
        "parent": parent,
        "children": children,
        "attendance_records": attendance_records,
    })