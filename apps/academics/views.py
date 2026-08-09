from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.audit.services import log_audit
from apps.core.decorators import role_required
from .forms import AcademicSessionForm, AcademicTermForm, SchoolClassForm, SessionRolloverForm, SubjectForm
from .models import AcademicSession, AcademicTerm, SchoolClass, Subject


def get_user_school(request):
    return request.user.school


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def academics_dashboard(request):
    school = get_user_school(request)

    context = {
        "sessions_count": AcademicSession.objects.filter(school=school).count(),
        "terms_count": AcademicTerm.objects.filter(school=school).count(),
        "classes_count": SchoolClass.objects.filter(school=school).count(),
        "subjects_count": Subject.objects.filter(school=school).count(),
        "current_session": AcademicSession.objects.filter(school=school, is_current=True).first(),
        "current_term": AcademicTerm.objects.filter(school=school, is_current=True).first(),
    }

    return render(request, "academics/dashboard.html", context)


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def session_list(request):
    school = get_user_school(request)
    query = request.GET.get("q", "").strip()

    sessions = AcademicSession.objects.filter(school=school)

    if query:
        sessions = sessions.filter(name__icontains=query)

    return render(request, "academics/session_list.html", {
        "sessions": sessions,
        "query": query,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def session_create(request):
    school = get_user_school(request)

    if request.method == "POST":
        form = AcademicSessionForm(request.POST)

        if form.is_valid():
            session = form.save(commit=False)
            session.school = school

            if session.is_current:
                AcademicSession.objects.filter(school=school).update(is_current=False)

            session.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.CREATE,
                module="academics",
                object_type="AcademicSession",
                object_id=session.id,
                description=f"Created academic session {session.name}",
            )

            messages.success(request, "Academic session created successfully.")
            return redirect("academic_session_list")
    else:
        form = AcademicSessionForm()

    return render(request, "academics/form.html", {
        "form": form,
        "title": "Create Academic Session",
        "back_url": "academic_session_list",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def session_update(request, pk):
    school = get_user_school(request)
    session = get_object_or_404(AcademicSession, pk=pk, school=school)

    if request.method == "POST":
        form = AcademicSessionForm(request.POST, instance=session)

        if form.is_valid():
            session = form.save(commit=False)

            if session.is_current:
                AcademicSession.objects.filter(school=school).exclude(pk=session.pk).update(is_current=False)

            session.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.UPDATE,
                module="academics",
                object_type="AcademicSession",
                object_id=session.id,
                description=f"Updated academic session {session.name}",
            )

            messages.success(request, "Academic session updated successfully.")
            return redirect("academic_session_list")
    else:
        form = AcademicSessionForm(instance=session)

    return render(request, "academics/form.html", {
        "form": form,
        "title": "Edit Academic Session",
        "back_url": "academic_session_list",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def term_list(request):
    school = get_user_school(request)
    terms = AcademicTerm.objects.filter(school=school).select_related("session")

    return render(request, "academics/term_list.html", {
        "terms": terms,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def term_create(request):
    school = get_user_school(request)

    if request.method == "POST":
        form = AcademicTermForm(request.POST, school=school)

        if form.is_valid():
            session = form.cleaned_data["session"]
            name = form.cleaned_data["name"]

            if AcademicTerm.objects.filter(
                school=school,
                session=session,
                name=name,
            ).exists():
                messages.error(
                    request,
                    "This academic term already exists for the selected session."
                )
                return render(request, "academics/form.html", {
                    "form": form,
                    "title": "Create Term",
                    "back_url": "academic_term_list",
                })

            term = form.save(commit=False)
            term.school = school
            term.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.CREATE,
                module="academics",
                object_type="AcademicTerm",
                object_id=term.id,
                description=f"Created academic term {term.get_name_display()}",
            )

            messages.success(request, "Academic term created successfully.")
            return redirect("academic_term_list")
    else:
        form = AcademicTermForm(school=school)

    return render(request, "academics/form.html", {
        "form": form,
        "title": "Create Academic Term",
        "back_url": "academic_term_list",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def term_update(request, pk):
    school = get_user_school(request)
    term = get_object_or_404(AcademicTerm, pk=pk, school=school)

    if request.method == "POST":
        form = AcademicTermForm(request.POST, instance=term, school=school)

        if form.is_valid():
            term = form.save(commit=False)

            if term.is_current:
                AcademicTerm.objects.filter(school=school).exclude(pk=term.pk).update(is_current=False)

            term.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.UPDATE,
                module="academics",
                object_type="AcademicTerm",
                object_id=term.id,
                description=f"Updated academic term {term.get_name_display()}",
            )

            messages.success(request, "Academic term updated successfully.")
            return redirect("academic_term_list")
    else:
        form = AcademicTermForm(instance=term, school=school)

    return render(request, "academics/form.html", {
        "form": form,
        "title": "Edit Academic Term",
        "back_url": "academic_term_list",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def class_list(request):
    school = get_user_school(request)
    query = request.GET.get("q", "").strip()

    classes = SchoolClass.objects.filter(school=school)

    if query:
        classes = classes.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query)
        )

    return render(request, "academics/class_list.html", {
        "classes": classes,
        "query": query,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def class_create(request):
    school = get_user_school(request)

    if request.method == "POST":
        form = SchoolClassForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data["name"].strip()

            if SchoolClass.objects.filter(
                school=school,
                name__iexact=name,
            ).exists():
                messages.error(
                    request,
                    f"The class '{name}' already exists for this school."
                )
                return render(request, "academics/form.html", {
                    "form": form,
                    "title": "Create Class",
                    "back_url": "academic_class_list",
                })

            school_class = form.save(commit=False)
            school_class.school = school
            school_class.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.CREATE,
                module="academics",
                object_type="SchoolClass",
                object_id=school_class.id,
                description=f"Created class {school_class.name}",
            )

            messages.success(request, "Class created successfully.")
            return redirect("academic_class_list")
    else:
        form = SchoolClassForm()

    return render(request, "academics/form.html", {
        "form": form,
        "title": "Create Class",
        "back_url": "academic_class_list",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def class_update(request, pk):
    school = get_user_school(request)
    school_class = get_object_or_404(SchoolClass, pk=pk, school=school)

    if request.method == "POST":
        form = SchoolClassForm(request.POST, instance=school_class)

        if form.is_valid():
            school_class = form.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.UPDATE,
                module="academics",
                object_type="SchoolClass",
                object_id=school_class.id,
                description=f"Updated class {school_class.name}",
            )

            messages.success(request, "Class updated successfully.")
            return redirect("academic_class_list")
    else:
        form = SchoolClassForm(instance=school_class)

    return render(request, "academics/form.html", {
        "form": form,
        "title": "Edit Class",
        "back_url": "academic_class_list",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def subject_list(request):
    school = get_user_school(request)
    query = request.GET.get("q", "").strip()

    subjects = Subject.objects.filter(school=school)

    if query:
        subjects = subjects.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(category__icontains=query)
        )

    return render(request, "academics/subject_list.html", {
        "subjects": subjects,
        "query": query,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def subject_create(request):
    school = get_user_school(request)

    if request.method == "POST":
        form = SubjectForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data["name"].strip()

            if Subject.objects.filter(
                school=school,
                name__iexact=name,
            ).exists():
                messages.error(
                    request,
                    f"The subject '{name}' already exists for this school."
                )
                return render(request, "academics/form.html", {
                    "form": form,
                    "title": "Create Subject",
                    "back_url": "academic_subject_list",
                })

            subject = form.save(commit=False)
            subject.school = school
            subject.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.CREATE,
                module="academics",
                object_type="Subject",
                object_id=subject.id,
                description=f"Created subject {subject.name}",
            )

            messages.success(request, "Subject created successfully.")
            return redirect("academic_subject_list")
    else:
        form = SubjectForm()

    return render(request, "academics/form.html", {
        "form": form,
        "title": "Create Subject",
        "back_url": "academic_subject_list",
    })




@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def subject_update(request, pk):
    school = get_user_school(request)
    subject = get_object_or_404(Subject, pk=pk, school=school)

    if request.method == "POST":
        form = SubjectForm(request.POST, instance=subject)

        if form.is_valid():
            subject = form.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.UPDATE,
                module="academics",
                object_type="Subject",
                object_id=subject.id,
                description=f"Updated subject {subject.name}",
            )

            messages.success(request, "Subject updated successfully.")
            return redirect("academic_subject_list")
    else:
        form = SubjectForm(instance=subject)

    return render(request, "academics/form.html", {
        "form": form,
        "title": "Edit Subject",
        "back_url": "academic_subject_list",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def session_rollover(request):
    school = get_user_school(request)

    current_session = AcademicSession.objects.filter(
        school=school,
        is_current=True,
    ).first()

    current_terms = AcademicTerm.objects.filter(
        school=school,
        session=current_session,
    ) if current_session else AcademicTerm.objects.none()

    if request.method == "POST":
        form = SessionRolloverForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                if current_session:
                    current_session.is_current = False
                    current_session.is_closed = True
                    current_session.closed_at = timezone.now()
                    current_session.save(update_fields=[
                        "is_current",
                        "is_closed",
                        "closed_at",
                    ])

                    current_terms.update(
                        is_current=False,
                        is_closed=True,
                        closed_at=timezone.now(),
                    )

                new_session = AcademicSession.objects.create(
                    school=school,
                    name=form.cleaned_data["new_session_name"],
                    start_date=form.cleaned_data["start_date"],
                    end_date=form.cleaned_data["end_date"],
                    is_current=True,
                    is_closed=False,
                )

                AcademicTerm.objects.create(
                    school=school,
                    session=new_session,
                    name=AcademicTerm.TermName.FIRST,
                    is_current=True,
                    is_closed=False,
                )

                AcademicTerm.objects.create(
                    school=school,
                    session=new_session,
                    name=AcademicTerm.TermName.SECOND,
                    is_current=False,
                    is_closed=False,
                )

                AcademicTerm.objects.create(
                    school=school,
                    session=new_session,
                    name=AcademicTerm.TermName.THIRD,
                    is_current=False,
                    is_closed=False,
                )

                log_audit(
                    request=request,
                    school=school,
                    action=AuditLog.Action.UPDATE,
                    module="academics",
                    object_type="AcademicSession",
                    description=f"Closed session and rolled over to {new_session.name}.",
                )

            messages.success(
                request,
                f"Session rollover completed. New session {new_session.name} is now active."
            )
            return redirect("academic_session_list")
    else:
        form = SessionRolloverForm()

    return render(request, "academics/session_rollover.html", {
        "form": form,
        "current_session": current_session,
        "current_terms": current_terms,
    })