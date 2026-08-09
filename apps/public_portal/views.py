from django.contrib import messages
from django.db.models import Sum, Avg
from django.shortcuts import get_object_or_404, redirect, render

from apps.academics.models import AcademicSession, AcademicTerm
from apps.audit.models import AuditLog
from apps.audit.services import log_audit
from apps.results.models import ResultEntry
from apps.schools.models import School
from apps.students.models import StudentProfile


def result_portal_home(request, portal_subpath):
    school = get_object_or_404(
        School,
        portal_subpath=portal_subpath,
        is_active=True,
        result_checker_enabled=True,
    )

    sessions = AcademicSession.objects.filter(school=school).order_by("-created_at")
    terms = AcademicTerm.objects.filter(school=school).select_related("session")

    return render(request, "public_portal/result_checker.html", {
        "school": school,
        "sessions": sessions,
        "terms": terms,
    })


def result_checker_submit(request, portal_subpath):
    school = get_object_or_404(
        School,
        portal_subpath=portal_subpath,
        is_active=True,
        result_checker_enabled=True,
    )

    if request.method != "POST":
        return redirect("public_result_portal", portal_subpath=portal_subpath)

    surname = request.POST.get("surname", "").strip()
    passkey = request.POST.get("passkey", "").strip().upper()
    session_id = request.POST.get("session")
    term_id = request.POST.get("term")

    student = StudentProfile.objects.filter(
        school=school,
        passkey=passkey,
        surname__iexact=surname,
        status=StudentProfile.Status.ACTIVE,
    ).first()

    if not student:
        log_audit(
            request=request,
            school=school,
            action=AuditLog.Action.SECURITY_BLOCK,
            module="public_portal",
            description=f"Failed public result check attempt for surname={surname}, passkey={passkey}",
        )

        messages.error(request, "Invalid surname or passkey.")
        return redirect("public_result_portal", portal_subpath=portal_subpath)

    session = get_object_or_404(AcademicSession, pk=session_id, school=school)
    term = get_object_or_404(AcademicTerm, pk=term_id, school=school, session=session)

    has_published_result = ResultEntry.objects.filter(
        school=school,
        student=student,
        session=session,
        term=term,
        is_published=True,
    ).exists()

    if not has_published_result:
        messages.warning(request, "Result is not yet published for this student.")
        return redirect("public_result_portal", portal_subpath=portal_subpath)

    return redirect(
        "public_student_result",
        portal_subpath=portal_subpath,
        token=student.result_token,
        session_id=session.id,
        term_id=term.id,
    )


def public_student_result(request, portal_subpath, token, session_id, term_id):
    school = get_object_or_404(
        School,
        portal_subpath=portal_subpath,
        is_active=True,
        result_checker_enabled=True,
    )

    student = get_object_or_404(
        StudentProfile.objects.select_related("school", "current_class"),
        school=school,
        result_token=token,
        status=StudentProfile.Status.ACTIVE,
    )

    session = get_object_or_404(AcademicSession, pk=session_id, school=school)
    term = get_object_or_404(AcademicTerm, pk=term_id, school=school, session=session)

    entries = ResultEntry.objects.filter(
        school=school,
        student=student,
        session=session,
        term=term,
        is_published=True,
    ).select_related("subject")

    total = entries.aggregate(total=Sum("total_score"))["total"] or 0
    average = entries.aggregate(avg=Avg("total_score"))["avg"] or 0

    return render(request, "public_portal/public_result.html", {
        "school": school,
        "student": student,
        "session": session,
        "term": term,
        "entries": entries,
        "total": total,
        "average": average,
    })


def verify_result_qr(request, token):
    student = get_object_or_404(
        StudentProfile.objects.select_related("school", "current_class"),
        result_token=token,
    )

    school = student.school

    if not school.is_active or not school.result_checker_enabled:
        return render(request, "public_portal/verification_failed.html", {
            "message": "This school result verification portal is currently unavailable."
        })

    latest_entry = ResultEntry.objects.filter(
        school=school,
        student=student,
        is_published=True,
    ).select_related("session", "term").order_by("-updated_at").first()

    if not latest_entry:
        return render(request, "public_portal/verification_failed.html", {
            "message": "No published result found for this verification code."
        })

    return redirect(
        "public_student_result",
        portal_subpath=school.portal_subpath,
        token=student.result_token,
        session_id=latest_entry.session.id,
        term_id=latest_entry.term.id,
    )