from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import User
from apps.academics.models import SchoolClass, Subject
from apps.audit.models import AuditLog
from apps.audit.services import log_audit
from apps.core.decorators import role_required
from apps.staffs.models import StaffProfile
from apps.students.models import StudentProfile
from .forms import LessonResourceForm
from .models import LessonResource


def get_user_school(request):
    return request.user.school


def teacher_classes_and_subjects(request):
    try:
        staff = request.user.staff_profile
        return staff.assigned_classes.all(), staff.assigned_subjects.all()
    except StaffProfile.DoesNotExist:
        return SchoolClass.objects.none(), Subject.objects.none()


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER, User.Role.STUDENT)
def lesson_dashboard(request):
    school = get_user_school(request)

    resources = LessonResource.objects.filter(school=school)

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
        resources = resources.filter(school_class__in=classes, subject__in=subjects)

    if request.user.is_student:
        student = get_object_or_404(StudentProfile, user=request.user, school=school)
        resources = resources.filter(
            school_class=student.current_class,
            is_published=True,
        )

    context = {
        "resources_count": resources.count(),
        "published_count": resources.filter(is_published=True).count(),
        "lesson_notes_count": resources.filter(resource_type=LessonResource.ResourceType.LESSON_NOTE).count(),
        "assignments_count": resources.filter(resource_type=LessonResource.ResourceType.ASSIGNMENT).count(),
    }

    return render(request, "lessons/dashboard.html", context)


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER, User.Role.STUDENT)
def lesson_list(request):
    school = get_user_school(request)

    query = request.GET.get("q", "").strip()
    class_id = request.GET.get("class", "").strip()
    subject_id = request.GET.get("subject", "").strip()
    resource_type = request.GET.get("type", "").strip()

    resources = LessonResource.objects.filter(
        school=school,
    ).select_related(
        "session",
        "term",
        "school_class",
        "subject",
        "uploaded_by",
    )

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
        resources = resources.filter(school_class__in=classes, subject__in=subjects)
        available_classes = classes
        available_subjects = subjects

    elif request.user.is_student:
        student = get_object_or_404(StudentProfile, user=request.user, school=school)
        resources = resources.filter(
            school_class=student.current_class,
            is_published=True,
        )
        available_classes = SchoolClass.objects.filter(pk=student.current_class_id)
        available_subjects = Subject.objects.filter(school=school, is_active=True)

    else:
        available_classes = SchoolClass.objects.filter(school=school, is_active=True)
        available_subjects = Subject.objects.filter(school=school, is_active=True)

    if query:
        resources = resources.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(subject__name__icontains=query)
            | Q(school_class__name__icontains=query)
        )

    if class_id:
        resources = resources.filter(school_class_id=class_id)

    if subject_id:
        resources = resources.filter(subject_id=subject_id)

    if resource_type:
        resources = resources.filter(resource_type=resource_type)

    return render(request, "lessons/lesson_list.html", {
        "resources": resources,
        "query": query,
        "class_id": class_id,
        "subject_id": subject_id,
        "resource_type": resource_type,
        "classes": available_classes,
        "subjects": available_subjects,
        "resource_types": LessonResource.ResourceType.choices,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def lesson_create(request):
    school = get_user_school(request)

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
    else:
        classes = None
        subjects = None

    if request.method == "POST":
        form = LessonResourceForm(
            request.POST,
            request.FILES,
            school=school,
            classes=classes,
            subjects=subjects,
        )

        if form.is_valid():
            resource = form.save(commit=False)
            resource.school = school
            resource.uploaded_by = request.user
            resource.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.CREATE,
                module="lessons",
                object_type="LessonResource",
                object_id=resource.id,
                description=f"Uploaded lesson resource: {resource.title}",
            )

            messages.success(request, "Lesson resource uploaded successfully.")
            return redirect("lesson_detail", pk=resource.pk)
    else:
        form = LessonResourceForm(school=school, classes=classes, subjects=subjects)

    return render(request, "lessons/lesson_form.html", {
        "form": form,
        "title": "Upload Lesson Resource",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER, User.Role.STUDENT)
def lesson_detail(request, pk):
    school = get_user_school(request)

    resources = LessonResource.objects.filter(school=school).select_related(
        "session",
        "term",
        "school_class",
        "subject",
        "uploaded_by",
    )

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
        resources = resources.filter(school_class__in=classes, subject__in=subjects)

    if request.user.is_student:
        student = get_object_or_404(StudentProfile, user=request.user, school=school)
        resources = resources.filter(
            school_class=student.current_class,
            is_published=True,
        )

    resource = get_object_or_404(resources, pk=pk)

    return render(request, "lessons/lesson_detail.html", {
        "resource": resource,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def lesson_update(request, pk):
    school = get_user_school(request)

    resources = LessonResource.objects.filter(school=school)

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
        resources = resources.filter(school_class__in=classes, subject__in=subjects)
    else:
        classes = None
        subjects = None

    resource = get_object_or_404(resources, pk=pk)

    if request.method == "POST":
        form = LessonResourceForm(
            request.POST,
            request.FILES,
            instance=resource,
            school=school,
            classes=classes,
            subjects=subjects,
        )

        if form.is_valid():
            resource = form.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.UPDATE,
                module="lessons",
                object_type="LessonResource",
                object_id=resource.id,
                description=f"Updated lesson resource: {resource.title}",
            )

            messages.success(request, "Lesson resource updated successfully.")
            return redirect("lesson_detail", pk=resource.pk)
    else:
        form = LessonResourceForm(
            instance=resource,
            school=school,
            classes=classes,
            subjects=subjects,
        )

    return render(request, "lessons/lesson_form.html", {
        "form": form,
        "title": "Edit Lesson Resource",
        "resource": resource,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN, User.Role.TEACHER)
def lesson_toggle_publish(request, pk):
    school = get_user_school(request)

    resources = LessonResource.objects.filter(school=school)

    if request.user.is_teacher:
        classes, subjects = teacher_classes_and_subjects(request)
        resources = resources.filter(school_class__in=classes, subject__in=subjects)

    resource = get_object_or_404(resources, pk=pk)

    resource.is_published = not resource.is_published
    resource.save(update_fields=["is_published", "updated_at"])

    log_audit(
        request=request,
        school=school,
        action=AuditLog.Action.UPDATE,
        module="lessons",
        object_type="LessonResource",
        object_id=resource.id,
        description=f"{'Published' if resource.is_published else 'Unpublished'} lesson resource: {resource.title}",
    )

    messages.success(
        request,
        f"Resource has been {'published' if resource.is_published else 'unpublished'}."
    )

    return redirect("lesson_detail", pk=resource.pk)