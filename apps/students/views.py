import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Avg, Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.models import User
from apps.academics.models import SchoolClass
from apps.audit.models import AuditLog
from apps.audit.services import log_audit
from apps.core.decorators import role_required
from .forms import StudentProfileForm, StudentClassMovementForm, SmartPromotionWizardForm
from .models import StudentProfile, StudentClassMovement
from apps.results.models import ResultEntry



def get_user_school(request):
    return request.user.school


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def student_list(request):
    school = get_user_school(request)
    query = request.GET.get("q", "").strip()
    class_id = request.GET.get("class", "").strip()
    status = request.GET.get("status", "").strip()

    students = StudentProfile.objects.filter(
        school=school,
    ).select_related("user", "current_class")

    if query:
        students = students.filter(
            Q(surname__icontains=query)
            | Q(first_name__icontains=query)
            | Q(middle_name__icontains=query)
            | Q(admission_number__icontains=query)
            | Q(passkey__icontains=query)
            | Q(guardian_phone__icontains=query)
        )

    if class_id:
        students = students.filter(current_class_id=class_id)

    if status:
        students = students.filter(status=status)

    classes = SchoolClass.objects.filter(school=school, is_active=True)

    return render(request, "students/student_list.html", {
        "students": students,
        "classes": classes,
        "query": query,
        "class_id": class_id,
        "status": status,
        "statuses": StudentProfile.Status.choices,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
@transaction.atomic
def student_create(request):
    school = get_user_school(request)

    if request.method == "POST":
        form = StudentProfileForm(request.POST, request.FILES, school=school)

        if form.is_valid():
            student = form.save(commit=False)

            student.school = school
            student.admission_number = StudentProfile.generate_admission_number(school)
            student.passkey = StudentProfile.generate_unique_passkey()

            username = student.admission_number.replace("/", "").lower()
            email = form.cleaned_data.get("guardian_email") or f"{username}@students.mutafs.local"
            password = form.cleaned_data.get("temporary_password") or "Passkey@123"

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=student.first_name,
                last_name=student.surname,
                role=User.Role.STUDENT,
                school=school,
                must_change_password=True,
                is_active=True,
            )

            student.user = user
            student.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.CREATE,
                module="students",
                object_type="StudentProfile",
                object_id=student.id,
                description=f"Created student {student.full_name}",
            )

            messages.success(
                request,
                f"Student created successfully. Admission No: {student.admission_number}, Passkey: {student.passkey}"
            )
            return redirect("student_detail", pk=student.pk)
    else:
        form = StudentProfileForm(school=school)

    return render(request, "students/student_form.html", {
        "form": form,
        "title": "Register Student",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def student_detail(request, pk):
    school = get_user_school(request)
    student = get_object_or_404(
        StudentProfile.objects.select_related("user", "school", "current_class"),
        pk=pk,
        school=school,
    )

    audit_logs = student.school.audit_logs.filter(
        object_type="StudentProfile",
        object_id=str(student.id),
    )[:10]

    return render(request, "students/student_detail.html", {
        "student": student,
        "audit_logs": audit_logs,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
@transaction.atomic
def student_update(request, pk):
    school = get_user_school(request)
    student = get_object_or_404(StudentProfile, pk=pk, school=school)

    if request.method == "POST":
        form = StudentProfileForm(
            request.POST,
            request.FILES,
            instance=student,
            school=school,
        )

        if form.is_valid():
            student = form.save()

            student.user.first_name = student.first_name
            student.user.last_name = student.surname
            student.user.email = student.guardian_email or student.user.email
            student.user.is_active = student.status == StudentProfile.Status.ACTIVE

            password = form.cleaned_data.get("temporary_password")
            if password:
                student.user.set_password(password)
                student.user.must_change_password = True

            student.user.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.UPDATE,
                module="students",
                object_type="StudentProfile",
                object_id=student.id,
                description=f"Updated student {student.full_name}",
            )

            messages.success(request, "Student updated successfully.")
            return redirect("student_detail", pk=student.pk)
    else:
        form = StudentProfileForm(instance=student, school=school)

    return render(request, "students/student_form.html", {
        "form": form,
        "title": "Edit Student",
        "student": student,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def student_export_csv(request):
    school = get_user_school(request)

    students = StudentProfile.objects.filter(
        school=school,
    ).select_related("current_class")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="students.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Admission Number",
        "Full Name",
        "Class",
        "Gender",
        "Status",
        "Passkey",
        "Guardian Name",
        "Guardian Phone",
        "Admission Date",
    ])

    for student in students:
        writer.writerow([
            student.admission_number,
            student.full_name,
            student.current_class.name if student.current_class else "",
            student.get_gender_display(),
            student.get_status_display(),
            student.passkey,
            student.guardian_name,
            student.guardian_phone,
            student.admission_date,
        ])

    log_audit(
        request=request,
        school=school,
        action=AuditLog.Action.EXPORT,
        module="students",
        description="Exported student CSV report.",
    )

    return response


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def student_passkey_card(request, pk):
    school = get_user_school(request)

    student = get_object_or_404(
        StudentProfile.objects.select_related("school", "current_class"),
        pk=pk,
        school=school,
    )

    return render(request, "students/passkey_card.html", {
        "student": student,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def class_passkey_cards(request, class_id):
    school = get_user_school(request)

    school_class = get_object_or_404(
        SchoolClass,
        pk=class_id,
        school=school,
    )

    students = StudentProfile.objects.filter(
        school=school,
        current_class=school_class,
        status=StudentProfile.Status.ACTIVE,
    ).select_related("current_class").order_by("surname", "first_name")

    return render(request, "students/passkey_cards_sheet.html", {
        "students": students,
        "school_class": school_class,
        "title": f"{school_class.name} Passkey Cards",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def school_passkey_cards(request):
    school = get_user_school(request)

    students = StudentProfile.objects.filter(
        school=school,
        status=StudentProfile.Status.ACTIVE,
    ).select_related("current_class").order_by(
        "current_class__position_order",
        "surname",
        "first_name",
    )

    return render(request, "students/passkey_cards_sheet.html", {
        "students": students,
        "school_class": None,
        "title": "School Passkey Cards",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def student_class_movement(request):
    school = get_user_school(request)

    if request.method == "POST":
        form = StudentClassMovementForm(request.POST, school=school)

        if form.is_valid():
            source_class = form.cleaned_data["source_class"]
            destination_class = form.cleaned_data["destination_class"]
            students = form.cleaned_data["students"]
            movement_type = form.cleaned_data["movement_type"]
            session = form.cleaned_data.get("session")
            term = form.cleaned_data.get("term")
            reason = form.cleaned_data.get("reason", "")

            moved_count = 0

            with transaction.atomic():
                for student in students:
                    if student.current_class_id != source_class.id:
                        continue

                    StudentClassMovement.objects.create(
                        school=school,
                        student=student,
                        from_class=source_class,
                        to_class=destination_class,
                        movement_type=movement_type,
                        session=session,
                        term=term,
                        reason=reason,
                        moved_by=request.user,
                    )

                    student.current_class = destination_class
                    student.save(update_fields=["current_class"])
                    moved_count += 1

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.UPDATE,
                module="students",
                object_type="StudentClassMovement",
                description=f"Moved {moved_count} student(s) from {source_class} to {destination_class}.",
            )

            messages.success(
                request,
                f"{moved_count} student(s) moved successfully."
            )
            return redirect("student_class_movement")
    else:
        form = StudentClassMovementForm(school=school)

    movements = StudentClassMovement.objects.filter(
        school=school,
    ).select_related(
        "student",
        "from_class",
        "to_class",
        "session",
        "term",
        "moved_by",
    )[:50]

    return render(request, "students/class_movement.html", {
        "form": form,
        "movements": movements,
    })


def build_promotion_preview(
    *,
    school,
    source_class,
    session,
    term,
    min_average_for_promotion,
    max_failed_subjects,
):
    students = StudentProfile.objects.filter(
        school=school,
        current_class=source_class,
        status=StudentProfile.Status.ACTIVE,
    ).order_by("surname", "first_name")

    preview = []

    for student in students:
        entries = ResultEntry.objects.filter(
            school=school,
            student=student,
            session=session,
            term=term,
            school_class=source_class,
            is_published=True,
        )

        total = entries.aggregate(total=Sum("total_score"))["total"] or 0
        average = entries.aggregate(avg=Avg("total_score"))["avg"] or 0
        subject_count = entries.count()
        failed_subjects = entries.filter(total_score__lt=40).count()

        if subject_count == 0:
            recommendation = "NO_RESULT"
            movement_type = StudentClassMovement.MovementType.REPEAT
        elif average >= min_average_for_promotion and failed_subjects <= max_failed_subjects:
            recommendation = "PROMOTE"
            movement_type = StudentClassMovement.MovementType.PROMOTION
        elif average >= 45:
            recommendation = "PROBATION"
            movement_type = StudentClassMovement.MovementType.PROMOTION
        else:
            recommendation = "REPEAT"
            movement_type = StudentClassMovement.MovementType.REPEAT

        preview.append({
            "student": student,
            "total": total,
            "average": average,
            "subject_count": subject_count,
            "failed_subjects": failed_subjects,
            "recommendation": recommendation,
            "movement_type": movement_type,
        })

    return preview


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def smart_promotion_wizard(request):
    school = get_user_school(request)
    preview = None

    if request.method == "POST":
        form = SmartPromotionWizardForm(request.POST, school=school)

        if form.is_valid():
            source_class = form.cleaned_data["source_class"]
            destination_class = form.cleaned_data["destination_class"]
            session = form.cleaned_data["session"]
            term = form.cleaned_data["term"]
            min_average_for_promotion = form.cleaned_data["min_average_for_promotion"]
            max_failed_subjects = form.cleaned_data["max_failed_subjects"]
            reason = form.cleaned_data.get("reason", "")

            preview = build_promotion_preview(
                school=school,
                source_class=source_class,
                session=session,
                term=term,
                min_average_for_promotion=min_average_for_promotion,
                max_failed_subjects=max_failed_subjects,
            )

            if request.POST.get("action") == "confirm":
                moved_count = 0
                repeated_count = 0

                with transaction.atomic():
                    for item in preview:
                        student = item["student"]

                        if item["recommendation"] in ["PROMOTE", "PROBATION"]:
                            to_class = destination_class
                            movement_type = item["movement_type"]
                        else:
                            to_class = source_class
                            movement_type = StudentClassMovement.MovementType.REPEAT

                        StudentClassMovement.objects.create(
                            school=school,
                            student=student,
                            from_class=source_class,
                            to_class=to_class,
                            movement_type=movement_type,
                            session=session,
                            term=term,
                            reason=reason,
                            moved_by=request.user,
                        )

                        student.current_class = to_class
                        student.save(update_fields=["current_class"])

                        if to_class == destination_class:
                            moved_count += 1
                        else:
                            repeated_count += 1

                log_audit(
                    request=request,
                    school=school,
                    action=AuditLog.Action.UPDATE,
                    module="students",
                    object_type="SmartPromotionWizard",
                    description=(
                        f"Smart promotion completed from {source_class} "
                        f"to {destination_class}. Promoted: {moved_count}, "
                        f"Repeated: {repeated_count}."
                    ),
                )

                messages.success(
                    request,
                    f"Promotion completed. Promoted: {moved_count}, Repeated: {repeated_count}."
                )
                return redirect("smart_promotion_wizard")
    else:
        form = SmartPromotionWizardForm(school=school)

    return render(request, "students/smart_promotion_wizard.html", {
        "form": form,
        "preview": preview,
    })