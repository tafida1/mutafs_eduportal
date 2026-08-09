import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from apps.students.models import StudentProfile
from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.audit.services import log_audit
from apps.core.decorators import role_required
from .forms import StaffProfileForm
from .models import StaffProfile
from datetime import datetime
from apps.results.models import ResultEntry
from apps.lessons.models import LessonResource
from apps.notifications.models import UserNotification
from apps.timetable.models import TimetableEntry



def get_user_school(request):
    return request.user.school


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def staff_list(request):
    school = get_user_school(request)
    query = request.GET.get("q", "").strip()
    staff_type = request.GET.get("type", "").strip()
    status = request.GET.get("status", "").strip()

    staffs = StaffProfile.objects.filter(
        school=school,
    ).select_related("user").prefetch_related("assigned_classes", "assigned_subjects")

    if query:
        staffs = staffs.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__email__icontains=query)
            | Q(staff_id__icontains=query)
            | Q(phone__icontains=query)
            | Q(designation__icontains=query)
        )

    if staff_type:
        staffs = staffs.filter(staff_type=staff_type)

    if status:
        staffs = staffs.filter(status=status)

    return render(request, "staffs/staff_list.html", {
        "staffs": staffs,
        "query": query,
        "staff_type": staff_type,
        "status": status,
        "staff_types": StaffProfile.StaffType.choices,
        "statuses": StaffProfile.Status.choices,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
@transaction.atomic
def staff_create(request):
    school = get_user_school(request)

    if request.method == "POST":
        form = StaffProfileForm(request.POST, request.FILES, school=school)

        if form.is_valid():
            password = form.cleaned_data.get("temporary_password") or "Staff@123"

            role = (
                User.Role.TEACHER
                if form.cleaned_data["staff_type"] == StaffProfile.StaffType.TEACHING
                else User.Role.SCHOOL_ADMIN
            )

            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data.get("email") or f'{form.cleaned_data["username"]}@staff.mutafs.local',
                password=password,
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                role=role,
                school=school,
                must_change_password=True,
                is_active=form.cleaned_data["status"] == StaffProfile.Status.ACTIVE,
            )

            staff = form.save(commit=False)
            staff.user = user
            staff.school = school
            staff.staff_id = StaffProfile.generate_staff_id(school)
            staff.save()
            form.save_m2m()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.CREATE,
                module="staffs",
                object_type="StaffProfile",
                object_id=staff.id,
                description=f"Created staff profile {staff.full_name}",
            )

            messages.success(request, f"Staff created successfully. Staff ID: {staff.staff_id}")
            return redirect("staff_detail", pk=staff.pk)
    else:
        form = StaffProfileForm(school=school)

    return render(request, "staffs/staff_form.html", {
        "form": form,
        "title": "Create Staff / Teacher",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def staff_detail(request, pk):
    school = get_user_school(request)

    staff = get_object_or_404(
        StaffProfile.objects.select_related("user", "school").prefetch_related(
            "assigned_classes",
            "assigned_subjects",
        ),
        pk=pk,
        school=school,
    )

    audit_logs = school.audit_logs.filter(
        object_type="StaffProfile",
        object_id=str(staff.id),
    )[:10]

    return render(request, "staffs/staff_detail.html", {
        "staff": staff,
        "audit_logs": audit_logs,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
@transaction.atomic
def staff_update(request, pk):
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, pk=pk, school=school)

    if request.method == "POST":
        form = StaffProfileForm(
            request.POST,
            request.FILES,
            instance=staff,
            school=school,
        )

        if form.is_valid():
            staff = form.save(commit=False)

            user = staff.user
            user.username = form.cleaned_data["username"]
            user.email = form.cleaned_data.get("email") or user.email
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.role = (
                User.Role.TEACHER
                if staff.staff_type == StaffProfile.StaffType.TEACHING
                else User.Role.SCHOOL_ADMIN
            )
            user.is_active = staff.status == StaffProfile.Status.ACTIVE

            password = form.cleaned_data.get("temporary_password")
            if password:
                user.set_password(password)
                user.must_change_password = True

            user.save()
            staff.save()
            form.save_m2m()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.UPDATE,
                module="staffs",
                object_type="StaffProfile",
                object_id=staff.id,
                description=f"Updated staff profile {staff.full_name}",
            )

            messages.success(request, "Staff updated successfully.")
            return redirect("staff_detail", pk=staff.pk)
    else:
        form = StaffProfileForm(instance=staff, school=school)

    return render(request, "staffs/staff_form.html", {
        "form": form,
        "title": "Edit Staff / Teacher",
        "staff": staff,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def staff_export_csv(request):
    school = get_user_school(request)

    staffs = StaffProfile.objects.filter(
        school=school,
    ).select_related("user").prefetch_related("assigned_classes", "assigned_subjects")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="staffs.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Staff ID",
        "Full Name",
        "Username",
        "Email",
        "Type",
        "Designation",
        "Phone",
        "Classes",
        "Subjects",
        "Status",
    ])

    for staff in staffs:
        writer.writerow([
            staff.staff_id,
            staff.full_name,
            staff.user.username,
            staff.user.email,
            staff.get_staff_type_display(),
            staff.designation,
            staff.phone,
            ", ".join([c.name for c in staff.assigned_classes.all()]),
            ", ".join([s.name for s in staff.assigned_subjects.all()]),
            staff.get_status_display(),
        ])

    log_audit(
        request=request,
        school=school,
        action=AuditLog.Action.EXPORT,
        module="staffs",
        description="Exported staff CSV report.",
    )

    return response


@login_required
@role_required(User.Role.TEACHER)
def teacher_workspace(request):
    school = get_user_school(request)

    teacher = get_object_or_404(
        StaffProfile.objects.prefetch_related(
            "assigned_classes",
            "assigned_subjects",
        ),
        user=request.user,
        school=school,
    )

    assigned_classes_qs = teacher.assigned_classes.filter(
        school=school,
        is_active=True,
    )

    assigned_subjects_qs = teacher.assigned_subjects.filter(
        school=school,
        is_active=True,
    )

    assigned_classes = assigned_classes_qs.count()
    assigned_subjects = assigned_subjects_qs.count()

    total_students = StudentProfile.objects.filter(
        school=school,
        current_class__in=assigned_classes_qs,
        status=StudentProfile.Status.ACTIVE,
    ).count()

    total_results = ResultEntry.objects.filter(
        school=school,
        entered_by=request.user,
    ).count()

    total_resources = LessonResource.objects.filter(
        school=school,
        uploaded_by=request.user,
    ).count()

    today_day = datetime.now().strftime("%A").upper()

    today_timetable = TimetableEntry.objects.filter(
        school=school,
        teacher=teacher,
        time_slot__day=today_day,
        is_active=True,
    ).select_related(
        "subject",
        "school_class",
        "time_slot",
    ).order_by("time_slot__start_time")

    recent_resources = LessonResource.objects.filter(
        school=school,
        uploaded_by=request.user,
    ).select_related("subject").order_by("-created_at")[:5]

    recent_notifications = UserNotification.objects.filter(
        user=request.user,
        announcement__is_active=True,
    ).select_related("announcement").order_by("-created_at")[:5]

    context = {
        "teacher": teacher,
        "assigned_classes": assigned_classes,
        "assigned_subjects": assigned_subjects,
        "assigned_classes_list": assigned_classes_qs,
        "assigned_subjects_list": assigned_subjects_qs,
        "total_students": total_students,
        "total_results": total_results,
        "total_resources": total_resources,
        "today_timetable": today_timetable,
        "recent_resources": recent_resources,
        "recent_notifications": recent_notifications,
    }

    return render(
        request,
        "staffs/teacher_workspace.html",
        context,
    )


@login_required
@role_required(User.Role.TEACHER)
def teacher_my_classes(request):
    school = get_user_school(request)

    staff = get_object_or_404(
        StaffProfile.objects.prefetch_related(
            "assigned_classes",
            "assigned_subjects",
        ),
        user=request.user,
        school=school,
    )

    assigned_classes = staff.assigned_classes.filter(
        school=school,
        is_active=True,
    ).order_by("position_order", "name")

    return render(request, "staffs/teacher_my_classes.html", {
        "staff": staff,
        "assigned_classes": assigned_classes,
    })


@login_required
@role_required(User.Role.TEACHER)
def teacher_class_students(request, class_id):
    school = get_user_school(request)

    staff = get_object_or_404(
        StaffProfile.objects.prefetch_related("assigned_classes"),
        user=request.user,
        school=school,
    )

    school_class = get_object_or_404(
        staff.assigned_classes.filter(
            school=school,
            is_active=True,
        ),
        pk=class_id,
    )

    students = StudentProfile.objects.filter(
        school=school,
        current_class=school_class,
        status=StudentProfile.Status.ACTIVE,
    ).select_related("user", "current_class").order_by(
        "surname",
        "first_name",
    )

    return render(request, "staffs/teacher_class_students.html", {
        "staff": staff,
        "school_class": school_class,
        "students": students,
    })


@login_required
@role_required(User.Role.TEACHER)
def teacher_my_subjects(request):
    school = get_user_school(request)

    staff = get_object_or_404(
        StaffProfile.objects.prefetch_related(
            "assigned_classes",
            "assigned_subjects",
        ),
        user=request.user,
        school=school,
    )

    assigned_subjects = staff.assigned_subjects.filter(
        school=school,
        is_active=True,
    ).order_by("name")

    return render(request, "staffs/teacher_my_subjects.html", {
        "staff": staff,
        "assigned_subjects": assigned_subjects,
        "assigned_classes": staff.assigned_classes.filter(
            school=school,
            is_active=True,
        ),
    })
    