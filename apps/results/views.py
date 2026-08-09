from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Count, Q, Max, Min
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from apps.accounts.models import User
from apps.academics.models import AcademicSession, AcademicTerm, SchoolClass, Subject
from apps.audit.models import AuditLog
from apps.audit.services import log_audit
from apps.core.decorators import role_required
from apps.staffs.models import StaffProfile
from apps.students.models import StudentProfile
from .forms import GradeScaleForm, ResultSetupForm, PublicResultCheckForm
from .models import GradeScale, ResultEntry
from apps.results.services import recompute_class_result_intelligence
from apps.finance.models import StudentInvoice
from apps.schools.models import School
from apps.attendance.utils import get_student_attendance_summary


def get_user_school(request):
    return request.user.school


def teacher_classes_and_subjects(request):
    try:
        staff = request.user.staff_profile
        return staff.assigned_classes.all(), staff.assigned_subjects.all()
    except StaffProfile.DoesNotExist:
        return SchoolClass.objects.none(), Subject.objects.none()


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def result_dashboard(request):
    school = get_user_school(request)

    entries = ResultEntry.objects.filter(school=school)

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
        entries = entries.filter(school_class__in=classes, subject__in=subjects)

    context = {
        "total_entries": entries.count(),
        "published_entries": entries.filter(is_published=True).count(),
        "unpublished_entries": entries.filter(is_published=False).count(),
        "grade_scales_count": GradeScale.objects.filter(school=school).count(),
    }

    return render(request, "results/dashboard.html", context)


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def grade_scale_list(request):
    school = get_user_school(request)
    scales = GradeScale.objects.filter(school=school)

    return render(request, "results/grade_scale_list.html", {
        "scales": scales,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def grade_scale_create(request):
    school = get_user_school(request)

    if request.method == "POST":
        form = GradeScaleForm(request.POST)

        if form.is_valid():
            scale = form.save(commit=False)
            scale.school = school
            scale.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.CREATE,
                module="results",
                object_type="GradeScale",
                object_id=scale.id,
                description=f"Created grade scale {scale.grade}",
            )

            messages.success(request, "Grade scale created successfully.")
            return redirect("grade_scale_list")
    else:
        form = GradeScaleForm()

    return render(request, "results/form.html", {
        "form": form,
        "title": "Create Grade Scale",
        "back_url": "grade_scale_list",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def grade_scale_update(request, pk):
    school = get_user_school(request)
    scale = get_object_or_404(GradeScale, pk=pk, school=school)

    if request.method == "POST":
        form = GradeScaleForm(request.POST, instance=scale)

        if form.is_valid():
            scale = form.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.UPDATE,
                module="results",
                object_type="GradeScale",
                object_id=scale.id,
                description=f"Updated grade scale {scale.grade}",
            )

            messages.success(request, "Grade scale updated successfully.")
            return redirect("grade_scale_list")
    else:
        form = GradeScaleForm(instance=scale)

    return render(request, "results/form.html", {
        "form": form,
        "title": "Edit Grade Scale",
        "back_url": "grade_scale_list",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def seed_default_grade_scales(request):
    school = get_user_school(request)

    defaults = [
        ("A", 70, 100, "Excellent"),
        ("B", 60, 69, "Very Good"),
        ("C", 50, 59, "Good"),
        ("D", 45, 49, "Fair"),
        ("E", 40, 44, "Pass"),
        ("F", 0, 39, "Fail"),
    ]

    for grade, min_score, max_score, remark in defaults:
        GradeScale.objects.update_or_create(
            school=school,
            grade=grade,
            defaults={
                "min_score": min_score,
                "max_score": max_score,
                "remark": remark,
            },
        )

    log_audit(
        request=request,
        school=school,
        action=AuditLog.Action.CREATE,
        module="results",
        description="Seeded default grade scales.",
    )

    messages.success(request, "Default grade scales created successfully.")
    return redirect("grade_scale_list")


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def result_setup(request):
    school = get_user_school(request)

    sessions = AcademicSession.objects.filter(school=school)
    terms = AcademicTerm.objects.filter(school=school)

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
    else:
        classes = SchoolClass.objects.filter(school=school, is_active=True)
        subjects = Subject.objects.filter(school=school, is_active=True)

    if request.method == "POST":
        form = ResultSetupForm(
            request.POST,
            sessions=sessions,
            terms=terms,
            classes=classes,
            subjects=subjects,
        )

        if form.is_valid():
            return redirect(
                "result_entry",
                session_id=form.cleaned_data["session"].id,
                term_id=form.cleaned_data["term"].id,
                class_id=form.cleaned_data["school_class"].id,
                subject_id=form.cleaned_data["subject"].id,
            )
    else:
        form = ResultSetupForm(
            sessions=sessions,
            terms=terms,
            classes=classes,
            subjects=subjects,
        )

    return render(request, "results/result_setup.html", {
        "form": form,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def result_entry(request, session_id, term_id, class_id, subject_id):
    school = get_user_school(request)

    session = get_object_or_404(AcademicSession, pk=session_id, school=school)
    term = get_object_or_404(AcademicTerm, pk=term_id, school=school)

    if session.is_closed or term.is_closed:
        messages.error(
            request,
            "This session or term is closed. Results can no longer be edited."
        )
        return redirect("result_dashboard")

    if request.user.is_teacher:
        allowed_classes, allowed_subjects = teacher_classes_and_subjects(request)
        school_class = get_object_or_404(allowed_classes, pk=class_id)
        subject = get_object_or_404(allowed_subjects, pk=subject_id)
    else:
        school_class = get_object_or_404(SchoolClass, pk=class_id, school=school)
        subject = get_object_or_404(Subject, pk=subject_id, school=school)

    students = StudentProfile.objects.filter(
        school=school,
        current_class=school_class,
        status=StudentProfile.Status.ACTIVE,
    ).order_by("surname", "first_name")

    if request.method == "POST":
        for student in students:
            ca = request.POST.get(f"ca_{student.id}", "0") or "0"
            exam = request.POST.get(f"exam_{student.id}", "0") or "0"

            try:
                ca = Decimal(ca)
                exam = Decimal(exam)
            except Exception:
                ca = Decimal("0")
                exam = Decimal("0")

            if ca < 0:
                ca = Decimal("0")
            if ca > 30:
                ca = Decimal("30")

            if exam < 0:
                exam = Decimal("0")
            if exam > 70:
                exam = Decimal("70")

            ResultEntry.objects.update_or_create(
                school=school,
                student=student,
                session=session,
                term=term,
                subject=subject,
                defaults={
                    "school_class": school_class,
                    "ca_score": ca,
                    "exam_score": exam,
                    "entered_by": request.user,
                    "approval_status": ResultEntry.ApprovalStatus.PENDING,
                    "is_published": False,
                    "rejection_note": "",
                    "approved_by": None,
                    "approved_at": None,
                }
            )

        log_audit(
            request=request,
            school=school,
            action=AuditLog.Action.UPDATE,
            module="results",
            object_type="ResultEntry",
            description=f"Entered results for {school_class.name} - {subject.name} - {term.get_name_display()}",
        )

        recompute_class_result_intelligence(
            school=school,
            session=session,
            term=term,
            school_class=school_class,
        )

        messages.success(request, "Results saved successfully.")
        return redirect("result_class_summary", session_id=session.id, term_id=term.id, class_id=school_class.id)

    students_data = []

    existing_results = ResultEntry.objects.filter(
        school=school,
        subject=subject,
        session=session,
        term=term,
        school_class=school_class,
    ).exists()

    for student in students:

        result_entry = ResultEntry.objects.filter(
            school=school,
            student=student,
            subject=subject,
            session=session,
            term=term,
            school_class=school_class,
        ).first()

        ca_score = result_entry.ca_score if result_entry else 0
        exam_score = result_entry.exam_score if result_entry else 0

        students_data.append({
            "student": student,
            "result_entry": result_entry,
            "ca_score": ca_score,
            "exam_score": exam_score,
        })

    return render(request, "results/result_entry.html", {
        "session": session,
        "term": term,
        "school_class": school_class,
        "subject": subject,
        "students_data": students_data,
        "existing_results": existing_results,
    })





@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def result_class_summary(request, session_id, term_id, class_id):
    school = get_user_school(request)

    session = get_object_or_404(AcademicSession, pk=session_id, school=school)
    term = get_object_or_404(AcademicTerm, pk=term_id, school=school)

    if request.user.is_teacher:
        allowed_classes, allowed_subjects = teacher_classes_and_subjects(request)
        school_class = get_object_or_404(allowed_classes, pk=class_id)

        entries = ResultEntry.objects.filter(
            school=school,
            session=session,
            term=term,
            school_class=school_class,
            subject__in=allowed_subjects,
        )
    else:
        school_class = get_object_or_404(SchoolClass, pk=class_id, school=school)

        entries = ResultEntry.objects.filter(
            school=school,
            session=session,
            term=term,
            school_class=school_class,
        )

    pending_count = entries.filter(
        approval_status=ResultEntry.ApprovalStatus.PENDING
    ).count()

    approved_count = entries.filter(
        approval_status=ResultEntry.ApprovalStatus.APPROVED
    ).count()

    rejected_count = entries.filter(
        approval_status=ResultEntry.ApprovalStatus.REJECTED
    ).count()

    published_count = entries.filter(is_published=True).count()

    student_summaries = entries.values(
        "student",
        "student__surname",
        "student__first_name",
        "student__middle_name",
        "student__admission_number",
    ).annotate(
        grand_total=Sum("total_score"),
        average_score=Avg("total_score"),
        subjects_count=Count("subject"),
    ).order_by("-grand_total")

    return render(request, "results/class_summary.html", {
        "session": session,
        "term": term,
        "school_class": school_class,
        "student_summaries": student_summaries,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "published_count": published_count,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def publish_class_result(request, session_id, term_id, class_id):
    school = get_user_school(request)

    session = get_object_or_404(AcademicSession, pk=session_id, school=school)
    term = get_object_or_404(AcademicTerm, pk=term_id, school=school)
    school_class = get_object_or_404(SchoolClass, pk=class_id, school=school)

    approved_results = ResultEntry.objects.filter(
        school=school,
        session=session,
        term=term,
        school_class=school_class,
        approval_status=ResultEntry.ApprovalStatus.APPROVED,
    )

    if not approved_results.exists():
        messages.error(
            request,
            "You cannot publish this class result until it has been approved."
        )
        return redirect(
            "result_class_summary",
            session_id=session.id,
            term_id=term.id,
            class_id=school_class.id,
        )

    approved_results.update(is_published=True)

    log_audit(
        request=request,
        school=school,
        action=AuditLog.Action.RESULT_PUBLISHED,
        module="results",
        object_type="ResultEntry",
        description=f"Published results for {school_class.name} - {term.get_name_display()}",
    )

    recompute_class_result_intelligence(
        school=school,
        session=session,
        term=term,
        school_class=school_class,
    )

    messages.success(request, "Class results published successfully.")
    return redirect("result_class_summary", session_id=session.id, term_id=term.id, class_id=school_class.id)


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def unpublish_class_result(request, session_id, term_id, class_id):
    school = get_user_school(request)

    session = get_object_or_404(AcademicSession, pk=session_id, school=school)
    term = get_object_or_404(AcademicTerm, pk=term_id, school=school)
    school_class = get_object_or_404(SchoolClass, pk=class_id, school=school)

    ResultEntry.objects.filter(
        school=school,
        session=session,
        term=term,
        school_class=school_class,
    ).update(is_published=False)

    log_audit(
        request=request,
        school=school,
        action=AuditLog.Action.RESULT_UNPUBLISHED,
        module="results",
        object_type="ResultEntry",
        description=f"Unpublished results for {school_class.name} - {term.get_name_display()}",
    )

    messages.success(request, "Class results unpublished successfully.")
    return redirect("result_class_summary", session_id=session.id, term_id=term.id, class_id=school_class.id)


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def approve_class_result(request, session_id, term_id, class_id):
    school = get_user_school(request)

    session = get_object_or_404(AcademicSession, pk=session_id, school=school)
    term = get_object_or_404(AcademicTerm, pk=term_id, school=school)
    school_class = get_object_or_404(SchoolClass, pk=class_id, school=school)

    ResultEntry.objects.filter(
        school=school,
        session=session,
        term=term,
        school_class=school_class,
    ).update(
        approval_status=ResultEntry.ApprovalStatus.APPROVED,
        approved_by=request.user,
        approved_at=timezone.now(),
        rejection_note="",
    )

    log_audit(
        request=request,
        school=school,
        action=AuditLog.Action.UPDATE,
        module="results",
        object_type="ResultEntry",
        description=f"Approved results for {school_class.name} - {term.get_name_display()}",
    )

    recompute_class_result_intelligence(
        school=school,
        session=session,
        term=term,
        school_class=school_class,
    )

    messages.success(request, "Class results approved successfully.")
    return redirect(
        "result_class_summary",
        session_id=session.id,
        term_id=term.id,
        class_id=school_class.id,
    )


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def reject_class_result(request, session_id, term_id, class_id):
    school = get_user_school(request)

    session = get_object_or_404(AcademicSession, pk=session_id, school=school)
    term = get_object_or_404(AcademicTerm, pk=term_id, school=school)
    school_class = get_object_or_404(SchoolClass, pk=class_id, school=school)

    note = request.POST.get("rejection_note", "").strip()

    ResultEntry.objects.filter(
        school=school,
        session=session,
        term=term,
        school_class=school_class,
    ).update(
        approval_status=ResultEntry.ApprovalStatus.REJECTED,
        is_published=False,
        rejection_note=note or "Correction required.",
    )

    log_audit(
        request=request,
        school=school,
        action=AuditLog.Action.UPDATE,
        module="results",
        object_type="ResultEntry",
        description=f"Rejected results for correction: {school_class.name} - {term.get_name_display()}",
    )

    messages.warning(request, "Class results marked for correction.")
    return redirect(
        "result_class_summary",
        session_id=session.id,
        term_id=term.id,
        class_id=school_class.id,
    )


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.STUDENT, User.Role.PARENT)
def student_term_result(request, student_id, session_id, term_id):
    school = get_user_school(request)

    student = get_object_or_404(StudentProfile, pk=student_id, school=school)
    session = get_object_or_404(AcademicSession, pk=session_id, school=school)
    term = get_object_or_404(AcademicTerm, pk=term_id, school=school)

    if request.user.is_student and student.user != request.user:
        messages.error(request, "You cannot access another student's result.")
        return redirect("dashboard_router")

    if request.user.is_parent:
        parent = getattr(request.user, "parent_profile", None)
        if not parent or not parent.children.filter(pk=student.pk).exists():
            messages.error(request, "You cannot access this student's result.")
            return redirect("dashboard_router")

    entries = ResultEntry.objects.filter(
        school=school,
        student=student,
        session=session,
        term=term,
    ).select_related("subject")

    if not request.user.is_school_admin:
        entries = entries.filter(is_published=True)

    total = entries.aggregate(total=Sum("total_score"))["total"] or 0
    average = entries.aggregate(avg=Avg("total_score"))["avg"] or 0

    intelligence_entry = entries.order_by("-total_score").first()

    class_entries = ResultEntry.objects.filter(
        school=school,
        session=session,
        term=term,
        school_class=student.current_class,
        is_published=True,
    )

    student_totals = (
        class_entries
        .values("student")
        .annotate(total=Sum("total_score"))
        .order_by("-total")
    )

    class_position = None

    for index, item in enumerate(student_totals, start=1):
        if item["student"] == student.id:
            class_position = index
            break

    attendance_summary = get_student_attendance_summary(
        school=school,
        student=student,
        session=session,
        term=term,
    )

    return render(request, "results/student_term_result.html", {
        "student": student,
        "session": session,
        "term": term,
        "entries": entries,
        "total": total,
        "average": average,
        "intelligence_entry": intelligence_entry,
        "attendance_summary": attendance_summary,
        "class_position": class_position,
    })





@login_required
@role_required(User.Role.STUDENT)
def student_result_portal(request):

    school = request.user.school

    student = get_object_or_404(
        StudentProfile.objects.select_related(
            "user",
            "current_class",
        ),
        user=request.user,
        school=school,
    )

    results = ResultEntry.objects.filter(
        school=school,
        student=student,
        is_published=True,
    ).select_related(
        "session",
        "term",
        "school_class",
        "subject",
    ).order_by(
        "-session__start_date",
        "subject__name",
    )

    outstanding_invoice = StudentInvoice.objects.filter(
        school=school,
        student=student,
        balance__gt=0,
    ).exists()

    average_score = results.aggregate(
        avg=Avg("total_score")
    )["avg"] or 0

    highest_score = results.aggregate(
        high=Max("total_score")
    )["high"] or 0

    lowest_score = results.aggregate(
        low=Min("total_score")
    )["low"] or 0

    term_results = results.values(
        "session",
        "session__name",
        "term",
        "term__name",
    ).annotate(
        total=Sum("total_score"),
        average=Avg("total_score"),
        subjects_count=Count("subject"),
    ).order_by("-session__start_date", "term__name")

    return render(request, "results/student_portal.html", {
        "student": student,
        "results": results,
        "average_score": average_score,
        "highest_score": highest_score,
        "lowest_score": lowest_score,
        "outstanding_invoice": outstanding_invoice,
        "term_results": term_results,
    })


@login_required
@role_required(User.Role.PARENT)
def parent_result_portal(request):

    school = request.user.school

    parent = getattr(request.user, "parent_profile", None)

    if not parent:
        messages.error(request, "Parent profile not found.")
        return redirect("dashboard_router")

    children = parent.children.all()

    results = ResultEntry.objects.filter(
        school=school,
        student__in=children,
        is_published=True,
    ).select_related(
        "student",
        "session",
        "term",
        "school_class",
        "subject",
    ).order_by(
        "-session__start_date",
        "student__surname",
    )

    term_results = results.values(
        "student",
        "student__surname",
        "student__first_name",
        "student__middle_name",
        "student__admission_number",
        "session",
        "session__name",
        "term",
        "term__name",
    ).annotate(
        total=Sum("total_score"),
        average=Avg("total_score"),
        subjects_count=Count("subject"),
    ).order_by(
        "student__surname",
        "-session__start_date",
        "term__name",
    )

    return render(request, "results/parent_portal.html", {
        "parent": parent,
        "children": children,
        "results": results,
        "term_results": term_results,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def print_class_results(request, session_id, term_id, class_id):
    school = get_user_school(request)

    session = get_object_or_404(AcademicSession, pk=session_id, school=school)
    term = get_object_or_404(AcademicTerm, pk=term_id, school=school)
    school_class = get_object_or_404(SchoolClass, pk=class_id, school=school)

    students = StudentProfile.objects.filter(
        school=school,
        current_class=school_class,
        status=StudentProfile.Status.ACTIVE,
    ).select_related(
        "current_class",
    ).order_by(
        "surname",
        "first_name",
    )

    student_results = []

    for student in students:
        entries = ResultEntry.objects.filter(
            school=school,
            student=student,
            session=session,
            term=term,
            school_class=school_class,
        ).select_related(
            "subject",
        ).order_by(
            "subject__name",
        )

        total = entries.aggregate(total=Sum("total_score"))["total"] or 0
        average = entries.aggregate(avg=Avg("total_score"))["avg"] or 0

        intelligence_entry = entries.order_by("-total_score").first()

        student_results.append({
            "student": student,
            "entries": entries,
            "total": total,
            "average": average,
            "intelligence_entry": intelligence_entry,
            "attendance_summary": get_student_attendance_summary(
                school=school,
                student=student,
                session=session,
                term=term,
            ),
        })

    student_results.sort(key=lambda item: item["total"], reverse=True)

    for index, item in enumerate(student_results, start=1):
        item["class_position"] = index

    return render(request, "results/print_class_results.html", {
        "school": school,
        "session": session,
        "term": term,
        "school_class": school_class,
        "student_results": student_results,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def class_broadsheet(request, session_id, term_id, class_id):
    school = get_user_school(request)

    session = get_object_or_404(AcademicSession, pk=session_id, school=school)
    term = get_object_or_404(AcademicTerm, pk=term_id, school=school)

    if request.user.is_teacher:
        allowed_classes, allowed_subjects = teacher_classes_and_subjects(request)
        school_class = get_object_or_404(allowed_classes, pk=class_id)
        subjects = allowed_subjects.filter(is_active=True).order_by("name")
    else:
        school_class = get_object_or_404(SchoolClass, pk=class_id, school=school)
        subjects = Subject.objects.filter(
            school=school,
            is_active=True,
        ).order_by("name")

    recompute_class_result_intelligence(
        school=school,
        session=session,
        term=term,
        school_class=school_class,
    )

    students = StudentProfile.objects.filter(
        school=school,
        current_class=school_class,
        status=StudentProfile.Status.ACTIVE,
    ).order_by("surname", "first_name")

    entries = ResultEntry.objects.filter(
        school=school,
        session=session,
        term=term,
        school_class=school_class,
        student__in=students,
        subject__in=subjects,
    ).select_related("student", "subject")

    result_map = {}

    for entry in entries:
        result_map[(entry.student_id, entry.subject_id)] = entry

    broadsheet_rows = []

    for student in students:
        subject_results = []
        total = Decimal("0")
        subject_count = 0
        failed_subjects = 0

        for subject in subjects:
            entry = result_map.get((student.id, subject.id))

            if entry:
                score = entry.total_score or Decimal("0")
                total += score
                subject_count += 1

                if score < 40:
                    failed_subjects += 1

                subject_results.append({
                    "subject": subject,
                    "entry": entry,
                    "score": score,
                    "grade": entry.grade,
                })
            else:
                subject_results.append({
                    "subject": subject,
                    "entry": None,
                    "score": None,
                    "grade": "—",
                })

        average = total / subject_count if subject_count else Decimal("0")

        broadsheet_rows.append({
            "student": student,
            "subject_results": subject_results,
            "total": total,
            "average": average,
            "subject_count": subject_count,
            "failed_subjects": failed_subjects,
        })

    broadsheet_rows.sort(key=lambda x: x["total"], reverse=True)

    for index, row in enumerate(broadsheet_rows, start=1):
        row["position"] = index

    class_total = sum(row["total"] for row in broadsheet_rows)
    class_average = (
        class_total / len(broadsheet_rows)
        if broadsheet_rows else Decimal("0")
    )

    highest_average = max(
        [row["average"] for row in broadsheet_rows],
        default=Decimal("0"),
    )

    lowest_average = min(
        [row["average"] for row in broadsheet_rows],
        default=Decimal("0"),
    )

    return render(request, "results/class_broadsheet.html", {
        "school": school,
        "session": session,
        "term": term,
        "school_class": school_class,
        "subjects": subjects,
        "broadsheet_rows": broadsheet_rows,
        "class_average": class_average,
        "highest_average": highest_average,
        "lowest_average": lowest_average,
        "students_count": students.count(),
    })


def public_result_checker(request):
    selected_school = None

    if request.method == "POST":
        school_id = request.POST.get("school")

        try:
            selected_school = School.objects.get(
                id=school_id,
                is_active=True,
                result_checker_enabled=True,
            )
        except School.DoesNotExist:
            selected_school = None

        form = PublicResultCheckForm(
            request.POST,
            school=selected_school,
        )

        if form.is_valid():
            school = form.cleaned_data["school"]
            surname = form.cleaned_data["surname"].strip()
            passkey = form.cleaned_data["passkey"].strip()
            session = form.cleaned_data["session"]
            term = form.cleaned_data["term"]

            student = StudentProfile.objects.filter(
                school=school,
                surname__iexact=surname,
                passkey=passkey,
                status=StudentProfile.Status.ACTIVE,
            ).first()

            if not student:
                messages.error(request, "Invalid surname or passkey.")
                return render(request, "results/public_result_checker.html", {
                    "form": form,
                })

            entries = ResultEntry.objects.filter(
                school=school,
                student=student,
                session=session,
                term=term,
                is_published=True,
            ).select_related("subject")

            if not entries.exists():
                messages.error(request, "No published result found for the selected session and term.")
                return render(request, "results/public_result_checker.html", {
                    "form": form,
                })

            total = entries.aggregate(total=Sum("total_score"))["total"] or 0
            average = entries.aggregate(avg=Avg("total_score"))["avg"] or 0

            recompute_class_result_intelligence(
                school=school,
                session=session,
                term=term,
                school_class=student.current_class,
            )

            entries = ResultEntry.objects.filter(
                school=school,
                student=student,
                session=session,
                term=term,
                is_published=True,
            ).select_related("subject")

            intelligence_entry = entries.order_by("id").first()

            class_entries = ResultEntry.objects.filter(
                school=school,
                session=session,
                term=term,
                school_class=student.current_class,
                is_published=True,
            )

            student_totals = (
                class_entries
                .values("student")
                .annotate(total=Sum("total_score"))
                .order_by("-total")
            )

            class_position = None

            for index, item in enumerate(student_totals, start=1):
                if item["student"] == student.id:
                    class_position = index
                    break

            attendance_summary = get_student_attendance_summary(
                school=school,
                student=student,
                session=session,
                term=term,
            )

            return render(request, "results/public_result_detail.html", {
                "school": school,
                "student": student,
                "session": session,
                "term": term,
                "entries": entries,
                "total": total,
                "average": average,
                "intelligence_entry": intelligence_entry,
                "class_position": class_position,
                "attendance_summary": attendance_summary,
            })

    else:
        form = PublicResultCheckForm()

    return render(request, "results/public_result_checker.html", {
        "form": form,
    })


def verify_result(request, token):
    entry = ResultEntry.objects.filter(
        verification_token=token,
    ).select_related(
        "school",
        "student",
        "session",
        "term",
        "school_class",
    ).first()

    if not entry:
        return render(request, "results/verify_result.html", {
            "valid": False,
        })

    entries = ResultEntry.objects.filter(
        school=entry.school,
        student=entry.student,
        session=entry.session,
        term=entry.term,
        is_published=True,
    ).select_related("subject")

    valid = entries.exists() and entry.is_published

    total = entries.aggregate(total=Sum("total_score"))["total"] or 0
    average = entries.aggregate(avg=Avg("total_score"))["avg"] or 0

    return render(request, "results/verify_result.html", {
        "valid": valid,
        "entry": entry,
        "entries": entries,
        "student": entry.student,
        "school": entry.school,
        "session": entry.session,
        "term": entry.term,
        "total": total,
        "average": average,
    })