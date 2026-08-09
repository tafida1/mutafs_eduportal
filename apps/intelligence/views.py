from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404, render

from apps.accounts.models import User
from apps.core.decorators import role_required
from apps.students.models import StudentProfile

from .ai_services import generate_ai_academic_comment, generate_teacher_ai_content
from .forms import TeacherAssistantForm
from django.contrib import messages
from .services import (
    get_student_intelligence,
    get_school_risk_students,
    calculate_student_risk_score,
)


@login_required
@role_required(User.Role.STUDENT)
def my_academic_insight(request):
    student = get_object_or_404(
        StudentProfile,
        user=request.user,
        school=request.user.school,
    )

    insight = get_student_intelligence(student)

    ai_comment = generate_ai_academic_comment(
        student=student,
        insight=insight,
    )

    return render(request, "intelligence/student_insight.html", {
        "student": student,
        "insight": insight,
        "ai_comment": ai_comment,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER, User.Role.PARENT)
def student_academic_insight(request, student_id):
    student = get_object_or_404(
        StudentProfile,
        pk=student_id,
        school=request.user.school,
    )

    if request.user.is_parent:
        parent = getattr(request.user, "parent_profile", None)

        if not parent or not parent.children.filter(pk=student.pk).exists():
            messages.error(request, "You cannot access this student's academic insight.")
            return redirect("parent_portal_dashboard")

    insight = get_student_intelligence(student)

    ai_comment = generate_ai_academic_comment(
        student=student,
        insight=insight,
    )

    return render(request, "intelligence/student_insight.html", {
        "student": student,
        "insight": insight,
        "ai_comment": ai_comment,
    })




@login_required
@role_required(User.Role.TEACHER, User.Role.SCHOOL_ADMIN)
def teacher_ai_assistant(request):
    generated_content = None

    if request.method == "POST":
        form = TeacherAssistantForm(request.POST)

        if form.is_valid():
            generated_content = generate_teacher_ai_content(
                task_type=form.cleaned_data["task_type"],
                subject=form.cleaned_data["subject"],
                school_class=form.cleaned_data["school_class"],
                topic=form.cleaned_data["topic"],
                extra_instruction=form.cleaned_data["extra_instruction"],
            )
    else:
        form = TeacherAssistantForm()

    return render(request, "intelligence/teacher_ai_assistant.html", {
        "form": form,
        "generated_content": generated_content,
    })



@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def academic_risk_dashboard(request):
    school = request.user.school

    risk_rows = get_school_risk_students(school)

    critical_count = len([r for r in risk_rows if r["risk_level"] == "CRITICAL"])
    high_count = len([r for r in risk_rows if r["risk_level"] == "HIGH"])
    medium_count = len([r for r in risk_rows if r["risk_level"] == "MEDIUM"])
    low_count = len([r for r in risk_rows if r["risk_level"] == "LOW"])

    return render(request, "intelligence/risk_dashboard.html", {
        "risk_rows": risk_rows,
        "critical_count": critical_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
    })


@login_required
@role_required(User.Role.STUDENT)
def my_risk_profile(request):
    student = get_object_or_404(
        StudentProfile,
        user=request.user,
        school=request.user.school,
    )

    risk = calculate_student_risk_score(student)

    return render(request, "intelligence/risk_profile.html", {
        "student": student,
        "risk": risk,
        "insight": risk["insight"],
    })