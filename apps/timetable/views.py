from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.audit.services import log_audit
from apps.core.decorators import role_required
from apps.staffs.models import StaffProfile
from apps.students.models import StudentProfile
from .forms import TimeSlotForm, TimetableEntryForm
from .models import TimeSlot, TimetableEntry


def get_user_school(request):
    return request.user.school


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER, User.Role.STUDENT)
def timetable_dashboard(request):
    school = get_user_school(request)

    entries = TimetableEntry.objects.filter(school=school, is_active=True)

    if request.user.is_teacher:
        staff = get_object_or_404(StaffProfile, user=request.user, school=school)
        entries = entries.filter(teacher=staff)

    if request.user.is_student:
        student = get_object_or_404(StudentProfile, user=request.user, school=school)
        entries = entries.filter(school_class=student.current_class)

    context = {
        "time_slots_count": TimeSlot.objects.filter(school=school, is_active=True).count(),
        "entries_count": entries.count(),
        "monday_count": entries.filter(time_slot__day=TimeSlot.Day.MONDAY).count(),
        "today_label": "Timetable Overview",
    }

    return render(request, "timetable/dashboard.html", context)


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def time_slot_list(request):
    school = get_user_school(request)

    slots = TimeSlot.objects.filter(school=school)

    return render(request, "timetable/time_slot_list.html", {
        "slots": slots,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def time_slot_create(request):
    school = get_user_school(request)

    if request.method == "POST":
        form = TimeSlotForm(request.POST)

        if form.is_valid():
            slot = form.save(commit=False)
            slot.school = school

            try:
                slot.full_clean()
                slot.save()
            except ValidationError as e:
                form.add_error(None, e)

            if slot.pk:
                log_audit(
                    request=request,
                    school=school,
                    action=AuditLog.Action.CREATE,
                    module="timetable",
                    object_type="TimeSlot",
                    object_id=slot.id,
                    description=f"Created time slot {slot}",
                )

                messages.success(request, "Time slot created successfully.")
                return redirect("time_slot_list")
    else:
        form = TimeSlotForm()

    return render(request, "timetable/form.html", {
        "form": form,
        "title": "Create Time Slot",
        "back_url": "time_slot_list",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def time_slot_update(request, pk):
    school = get_user_school(request)
    slot = get_object_or_404(TimeSlot, pk=pk, school=school)

    if request.method == "POST":
        form = TimeSlotForm(request.POST, instance=slot)

        if form.is_valid():
            slot = form.save(commit=False)

            try:
                slot.full_clean()
                slot.save()
            except ValidationError as e:
                form.add_error(None, e)

            if not form.errors:
                log_audit(
                    request=request,
                    school=school,
                    action=AuditLog.Action.UPDATE,
                    module="timetable",
                    object_type="TimeSlot",
                    object_id=slot.id,
                    description=f"Updated time slot {slot}",
                )

                messages.success(request, "Time slot updated successfully.")
                return redirect("time_slot_list")
    else:
        form = TimeSlotForm(instance=slot)

    return render(request, "timetable/form.html", {
        "form": form,
        "title": "Edit Time Slot",
        "back_url": "time_slot_list",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def timetable_entry_create(request):
    school = get_user_school(request)

    if request.method == "POST":
        form = TimetableEntryForm(request.POST, school=school)

        if form.is_valid():

            entry = form.save(commit=False)
            entry.school = school
            entry.created_by = request.user

            try:
                entry.full_clean()
                entry.save()

                log_audit(
                    request=request,
                    school=school,
                    action=AuditLog.Action.CREATE,
                    module="timetable",
                    object_type="TimetableEntry",
                    object_id=entry.id,
                    description=f"Created timetable entry for {entry.school_class.name}",
                )

                messages.success(
                    request,
                    "Timetable entry created successfully."
                )

                return redirect(
                    "timetable_class_view",
                    class_id=entry.school_class.id
                )

            except ValidationError as e:
                form.add_error(None, e)

    else:
        form = TimetableEntryForm(school=school)

    return render(request, "timetable/form.html", {
        "form": form,
        "title": "Create Timetable Entry",
        "back_url": "timetable_dashboard",
    })

    

@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def timetable_entry_update(request, pk):
    school = get_user_school(request)
    entry = get_object_or_404(TimetableEntry, pk=pk, school=school)

    if request.method == "POST":
        form = TimetableEntryForm(request.POST, instance=entry, school=school)

        if form.is_valid():
            entry = form.save(commit=False)

            try:
                entry.full_clean()
                entry.save()
            except ValidationError as e:
                form.add_error(None, e)

            if not form.errors:
                log_audit(
                    request=request,
                    school=school,
                    action=AuditLog.Action.UPDATE,
                    module="timetable",
                    object_type="TimetableEntry",
                    object_id=entry.id,
                    description=f"Updated timetable entry {entry.id}",
                )

                messages.success(request, "Timetable entry updated successfully.")
                return redirect("timetable_class_view", class_id=entry.school_class.id)
    else:
        form = TimetableEntryForm(instance=entry, school=school)

    return render(request, "timetable/form.html", {
        "form": form,
        "title": "Edit Timetable Entry",
        "back_url": "timetable_dashboard",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER, User.Role.STUDENT)
def timetable_class_view(request, class_id=None):
    school = get_user_school(request)

    if request.user.is_student:
        student = get_object_or_404(StudentProfile, user=request.user, school=school)
        school_class = student.current_class
    else:
        from apps.academics.models import SchoolClass
        school_class = get_object_or_404(SchoolClass, pk=class_id, school=school)

    entries = TimetableEntry.objects.filter(
        school=school,
        school_class=school_class,
        is_active=True,
    ).select_related("time_slot", "subject", "teacher", "teacher__user")

    days = TimeSlot.Day.choices

    return render(request, "timetable/class_timetable.html", {
        "school_class": school_class,
        "entries": entries,
        "days": days,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def teacher_timetable_view(request, staff_id=None):
    school = get_user_school(request)

    if request.user.is_teacher:
        staff = get_object_or_404(StaffProfile, user=request.user, school=school)
    else:
        staff = get_object_or_404(StaffProfile, pk=staff_id, school=school)

    entries = TimetableEntry.objects.filter(
        school=school,
        teacher=staff,
        is_active=True,
    ).select_related("time_slot", "subject", "school_class")

    return render(request, "timetable/teacher_timetable.html", {
        "staff": staff,
        "entries": entries,
        "days": TimeSlot.Day.choices,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def timetable_entry_list(request):
    school = get_user_school(request)
    query = request.GET.get("q", "").strip()

    entries = TimetableEntry.objects.filter(
        school=school,
    ).select_related("school_class", "subject", "teacher", "teacher__user", "time_slot")

    if query:
        entries = entries.filter(
            Q(school_class__name__icontains=query)
            | Q(subject__name__icontains=query)
            | Q(teacher__user__first_name__icontains=query)
            | Q(teacher__user__last_name__icontains=query)
            | Q(room__icontains=query)
        )

    return render(request, "timetable/entry_list.html", {
        "entries": entries,
        "query": query,
    })