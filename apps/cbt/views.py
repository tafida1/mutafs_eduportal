import random
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.academics.models import SchoolClass, Subject
from apps.audit.models import AuditLog
from apps.audit.services import log_audit
from apps.core.decorators import role_required
from apps.staffs.models import StaffProfile
from apps.students.models import StudentProfile
from .forms import CBTQuestionForm, CBTExamForm
from .models import CBTQuestion, CBTExam, CBTAttempt, CBTAttemptQuestion


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
def cbt_dashboard(request):
    school = get_user_school(request)

    questions = CBTQuestion.objects.filter(school=school)
    exams = CBTExam.objects.filter(school=school)
    attempts = CBTAttempt.objects.filter(school=school)

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
        questions = questions.filter(school_class__in=classes, subject__in=subjects)
        exams = exams.filter(school_class__in=classes, subject__in=subjects)
        attempts = attempts.filter(exam__school_class__in=classes, exam__subject__in=subjects)

    context = {
        "questions_count": questions.count(),
        "exams_count": exams.count(),
        "active_exams_count": exams.filter(is_active=True).count(),
        "attempts_count": attempts.count(),
        "average_score": attempts.filter(status=CBTAttempt.Status.SUBMITTED).aggregate(avg=Avg("percentage"))["avg"] or 0,
    }

    return render(request, "cbt/dashboard.html", context)


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def question_list(request):
    school = get_user_school(request)
    query = request.GET.get("q", "").strip()

    questions = CBTQuestion.objects.filter(school=school).select_related("school_class", "subject")

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
        questions = questions.filter(school_class__in=classes, subject__in=subjects)

    if query:
        questions = questions.filter(
            Q(question_text__icontains=query)
            | Q(subject__name__icontains=query)
            | Q(school_class__name__icontains=query)
        )

    return render(request, "cbt/question_list.html", {
        "questions": questions,
        "query": query,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def question_create(request):
    school = get_user_school(request)

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
    else:
        classes = None
        subjects = None

    if request.method == "POST":
        form = CBTQuestionForm(request.POST, school=school, classes=classes, subjects=subjects)

        if form.is_valid():
            question = form.save(commit=False)
            question.school = school
            question.created_by = request.user
            question.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.CREATE,
                module="cbt",
                object_type="CBTQuestion",
                object_id=question.id,
                description=f"Created CBT question for {question.subject.name}",
            )

            messages.success(request, "CBT question created successfully.")
            return redirect("cbt_question_list")
    else:
        form = CBTQuestionForm(school=school, classes=classes, subjects=subjects)

    return render(request, "cbt/question_form.html", {
        "form": form,
        "title": "Create CBT Question",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def question_update(request, pk):
    school = get_user_school(request)

    question_qs = CBTQuestion.objects.filter(school=school)

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
        question_qs = question_qs.filter(school_class__in=classes, subject__in=subjects)
    else:
        classes = None
        subjects = None

    question = get_object_or_404(question_qs, pk=pk)

    if request.method == "POST":
        form = CBTQuestionForm(
            request.POST,
            instance=question,
            school=school,
            classes=classes,
            subjects=subjects,
        )

        if form.is_valid():
            question = form.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.UPDATE,
                module="cbt",
                object_type="CBTQuestion",
                object_id=question.id,
                description=f"Updated CBT question {question.id}",
            )

            messages.success(request, "CBT question updated successfully.")
            return redirect("cbt_question_list")
    else:
        form = CBTQuestionForm(instance=question, school=school, classes=classes, subjects=subjects)

    return render(request, "cbt/question_form.html", {
        "form": form,
        "title": "Edit CBT Question",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def exam_list(request):
    school = get_user_school(request)
    query = request.GET.get("q", "").strip()

    exams = CBTExam.objects.filter(school=school).select_related(
        "school_class",
        "subject",
        "session",
        "term",
    ).annotate(attempt_count=Count("attempts"))

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
        exams = exams.filter(school_class__in=classes, subject__in=subjects)

    if query:
        exams = exams.filter(
            Q(title__icontains=query)
            | Q(subject__name__icontains=query)
            | Q(school_class__name__icontains=query)
        )

    return render(request, "cbt/exam_list.html", {
        "exams": exams,
        "query": query,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def exam_create(request):
    school = get_user_school(request)

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
    else:
        classes = None
        subjects = None

    if request.method == "POST":
        form = CBTExamForm(request.POST, school=school, classes=classes, subjects=subjects)

        if form.is_valid():
            exam = form.save(commit=False)
            exam.school = school
            exam.created_by = request.user
            exam.save()
            form.save_m2m()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.CREATE,
                module="cbt",
                object_type="CBTExam",
                object_id=exam.id,
                description=f"Created CBT exam {exam.title}",
            )

            messages.success(request, "CBT exam created successfully.")
            return redirect("cbt_exam_detail", pk=exam.pk)
    else:
        form = CBTExamForm(school=school, classes=classes, subjects=subjects)

    return render(request, "cbt/exam_form.html", {
        "form": form,
        "title": "Create CBT Exam",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def exam_detail(request, pk):
    school = get_user_school(request)

    exams = CBTExam.objects.filter(school=school).select_related(
        "school_class",
        "subject",
        "session",
        "term",
    ).prefetch_related("questions")

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
        exams = exams.filter(school_class__in=classes, subject__in=subjects)

    exam = get_object_or_404(exams, pk=pk)

    attempts = exam.attempts.select_related("student").order_by("-started_at")[:50]

    return render(request, "cbt/exam_detail.html", {
        "exam": exam,
        "attempts": attempts,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def exam_update(request, pk):
    school = get_user_school(request)

    exams = CBTExam.objects.filter(school=school)

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
        exams = exams.filter(school_class__in=classes, subject__in=subjects)
    else:
        classes = None
        subjects = None

    exam = get_object_or_404(exams, pk=pk)

    if request.method == "POST":
        form = CBTExamForm(
            request.POST,
            instance=exam,
            school=school,
            classes=classes,
            subjects=subjects,
        )

        if form.is_valid():
            exam = form.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.UPDATE,
                module="cbt",
                object_type="CBTExam",
                object_id=exam.id,
                description=f"Updated CBT exam {exam.title}",
            )

            messages.success(request, "CBT exam updated successfully.")
            return redirect("cbt_exam_detail", pk=exam.pk)
    else:
        form = CBTExamForm(instance=exam, school=school, classes=classes, subjects=subjects)

    return render(request, "cbt/exam_form.html", {
        "form": form,
        "title": "Edit CBT Exam",
        "exam": exam,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def exam_toggle_status(request, pk):
    school = get_user_school(request)

    exam = get_object_or_404(CBTExam, pk=pk, school=school)
    exam.is_active = not exam.is_active
    exam.save(update_fields=["is_active"])

    log_audit(
        request=request,
        school=school,
        action=AuditLog.Action.UPDATE,
        module="cbt",
        object_type="CBTExam",
        object_id=exam.id,
        description=f"{'Activated' if exam.is_active else 'Deactivated'} CBT exam {exam.title}",
    )

    messages.success(request, f"Exam has been {'activated' if exam.is_active else 'deactivated'}.")
    return redirect("cbt_exam_detail", pk=exam.pk)


@login_required
@role_required(User.Role.STUDENT)
def student_cbt_dashboard(request):
    school = get_user_school(request)
    student = get_object_or_404(StudentProfile, user=request.user, school=school)

    exams = CBTExam.objects.filter(
        school=school,
        school_class=student.current_class,
        is_active=True,
    ).select_related("subject", "session", "term")

    available_exams = [exam for exam in exams if exam.is_available()]

    attempts = CBTAttempt.objects.filter(
        school=school,
        student=student,
    ).select_related("exam", "exam__subject")

    return render(request, "cbt/student_dashboard.html", {
        "student": student,
        "available_exams": available_exams,
        "attempts": attempts,
    })


@login_required
@role_required(User.Role.STUDENT)
def start_exam(request, exam_id):
    school = get_user_school(request)
    student = get_object_or_404(StudentProfile, user=request.user, school=school)
    exam = get_object_or_404(CBTExam, pk=exam_id, school=school, school_class=student.current_class)

    if not exam.is_available():
        messages.error(request, "This exam is not currently available.")
        return redirect("student_cbt_dashboard")

    existing_submitted = CBTAttempt.objects.filter(
        school=school,
        student=student,
        exam=exam,
        status=CBTAttempt.Status.SUBMITTED,
    ).first()

    if existing_submitted and not exam.allow_retake:
        messages.warning(request, "You have already submitted this exam.")
        return redirect("cbt_attempt_result", attempt_id=existing_submitted.id)

    attempt = CBTAttempt.objects.create(
        school=school,
        student=student,
        exam=exam,
    )

    question_qs = list(exam.questions.filter(is_active=True))

    if exam.shuffle_questions:
        random.shuffle(question_qs)

    selected_questions = question_qs[:exam.total_questions]

    for question in selected_questions:
        CBTAttemptQuestion.objects.create(
            attempt=attempt,
            question=question,
        )

    log_audit(
        request=request,
        school=school,
        action=AuditLog.Action.CREATE,
        module="cbt",
        object_type="CBTAttempt",
        object_id=attempt.id,
        description=f"Started CBT exam {exam.title}",
    )

    return redirect("take_exam", attempt_id=attempt.id)


@login_required
@role_required(User.Role.STUDENT)
def take_exam(request, attempt_id):
    school = get_user_school(request)
    student = get_object_or_404(StudentProfile, user=request.user, school=school)

    attempt = get_object_or_404(
        CBTAttempt.objects.select_related("exam", "student"),
        pk=attempt_id,
        school=school,
        student=student,
    )

    if attempt.status == CBTAttempt.Status.SUBMITTED:
        return redirect("cbt_attempt_result", attempt_id=attempt.id)

    attempt_questions = list(
        attempt.attempt_questions.select_related("question").order_by("id")
    )

    total_questions = len(attempt_questions)

    if total_questions == 0:
        messages.error(request, "No questions found for this exam.")
        return redirect("student_cbt_dashboard")

    current_number = int(request.GET.get("q", 1))

    if current_number < 1:
        current_number = 1

    if current_number > total_questions:
        current_number = total_questions

    current_item = attempt_questions[current_number - 1]
    question = current_item.question

    if request.method == "POST":

        selected = request.POST.get("answer", "")

        if selected in ["A", "B", "C", "D"]:
            current_item.selected_option = selected
            current_item.is_correct = selected == question.correct_option
            current_item.save(update_fields=["selected_option", "is_correct"])

        if request.GET.get("submit") == "1":
            correct_count = attempt.attempt_questions.filter(is_correct=True).count()

            percentage = Decimal("0.00")
            if total_questions > 0:
                percentage = Decimal(correct_count * 100) / Decimal(total_questions)

            attempt.score = correct_count
            attempt.percentage = percentage
            attempt.status = CBTAttempt.Status.SUBMITTED
            attempt.submitted_at = timezone.now()
            attempt.save(update_fields=["score", "percentage", "status", "submitted_at"])

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.CBT_SUBMITTED,
                module="cbt",
                object_type="CBTAttempt",
                object_id=attempt.id,
                description=f"Submitted CBT exam {attempt.exam.title}",
            )

            messages.success(request, "Exam submitted successfully.")
            return redirect("cbt_attempt_result", attempt_id=attempt.id)

        if current_number < total_questions:
            return redirect(f"{request.path}?q={current_number + 1}")

        return redirect(f"{request.path}?q={current_number}")

    elapsed_seconds = int(
        (timezone.now() - attempt.started_at).total_seconds()
    )

    total_seconds = attempt.exam.duration_minutes * 60

    remaining_seconds = max(
        total_seconds - elapsed_seconds,
        0
    )

    question_palette = []

    for index, item in enumerate(attempt_questions, start=1):

        question_palette.append({
            "number": index,
            "is_answered": bool(item.selected_option),
            "is_review": False,
        })

    context = {
        "attempt": attempt,
        "question": question,
        "current_item": current_item,
        "current_number": current_number,
        "total_questions": total_questions,
        "remaining_seconds": remaining_seconds,
        "selected_option": current_item.selected_option,
        "previous_question": current_number - 1 if current_number > 1 else None,
        "next_question": current_number + 1 if current_number < total_questions else None,
        "question_palette": question_palette,
    }

    return render(
        request,
        "cbt/student/exam_shell.html",
        context,
    )

    

@login_required
@role_required(User.Role.STUDENT, User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def attempt_result(request, attempt_id):
    school = get_user_school(request)

    attempt_qs = CBTAttempt.objects.filter(school=school).select_related(
        "exam",
        "student",
        "exam__subject",
    )

    if request.user.is_student:
        student = get_object_or_404(StudentProfile, user=request.user, school=school)
        attempt_qs = attempt_qs.filter(student=student)

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
        attempt_qs = attempt_qs.filter(exam__school_class__in=classes, exam__subject__in=subjects)

    attempt = get_object_or_404(attempt_qs, pk=attempt_id)

    return render(request, "cbt/attempt_result.html", {
        "attempt": attempt,
        "attempt_questions": attempt.attempt_questions.select_related("question"),
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def cbt_attempts_report(request):
    school = get_user_school(request)
    query = request.GET.get("q", "").strip()

    attempts = CBTAttempt.objects.filter(
        school=school,
        status=CBTAttempt.Status.SUBMITTED,
    ).select_related("exam", "student", "exam__subject", "exam__school_class")

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
        attempts = attempts.filter(exam__school_class__in=classes, exam__subject__in=subjects)

    if query:
        attempts = attempts.filter(
            Q(student__surname__icontains=query)
            | Q(student__first_name__icontains=query)
            | Q(student__admission_number__icontains=query)
            | Q(exam__title__icontains=query)
            | Q(exam__subject__name__icontains=query)
        )

    return render(request, "cbt/attempts_report.html", {
        "attempts": attempts,
        "query": query,
    })