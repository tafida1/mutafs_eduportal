import csv
from io import TextIOWrapper
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from apps.accounts.models import User
from apps.core.decorators import role_required
from apps.students.models import StudentProfile
from apps.staffs.models import StaffProfile
from apps.parents.models import ParentProfile
from apps.cbt.models import CBTQuestion
from apps.academics.models import SchoolClass, Subject, AcademicSession, AcademicTerm
from apps.results.models import ResultEntry
from apps.finance.models import StudentInvoice
from .forms import StudentImportForm, StaffImportForm, ParentImportForm, CBTQuestionImportForm


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def data_tools_dashboard(request):
    return render(request, "data_tools/dashboard.html")


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def download_student_import_template(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="student_import_template.csv"'

    writer = csv.writer(response)

    writer.writerow([
        "admission_number",
        "surname",
        "first_name",
        "middle_name",
        "gender",
        "class_name",
        "guardian_phone",
        "status",
    ])

    writer.writerow([
        "ADM001",
        "Muhammad",
        "Aisha",
        "Sani",
        "FEMALE",
        "SSS 1",
        "08012345678",
        "ACTIVE",
    ])

    return response


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def export_students_csv(request):
    school = request.user.school

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="students_export.csv"'

    writer = csv.writer(response)

    writer.writerow([
        "admission_number",
        "surname",
        "first_name",
        "middle_name",
        "gender",
        "class",
        "guardian_phone",
        "status",
    ])

    students = StudentProfile.objects.filter(
        school=school,
    ).select_related(
        "current_class",
    ).order_by(
        "surname",
        "first_name",
    )

    for student in students:
        writer.writerow([
            student.admission_number,
            student.surname,
            student.first_name,
            student.middle_name,
            student.gender,
            student.current_class.name if student.current_class else "",
            student.guardian_phone,
            student.status,
        ])

    return response


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def import_students_csv(request):
    school = request.user.school

    if request.method == "POST":
        form = StudentImportForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = form.cleaned_data["file"]

            if not uploaded_file.name.endswith(".csv"):
                messages.error(request, "Only CSV files are supported for now.")
                return redirect("import_students_csv")

            decoded_file = TextIOWrapper(
                uploaded_file.file,
                encoding="utf-8",
            )

            reader = csv.DictReader(decoded_file)

            created_count = 0
            updated_count = 0
            error_rows = []

            required_columns = [
                "admission_number",
                "surname",
                "first_name",
                "gender",
                "class_name",
            ]

            missing_columns = [
                col for col in required_columns
                if col not in reader.fieldnames
            ]

            if missing_columns:
                messages.error(
                    request,
                    f"Missing required columns: {', '.join(missing_columns)}"
                )
                return redirect("import_students_csv")

            for index, row in enumerate(reader, start=2):
                try:
                    admission_number = row.get("admission_number", "").strip()
                    surname = row.get("surname", "").strip()
                    first_name = row.get("first_name", "").strip()
                    middle_name = row.get("middle_name", "").strip()
                    gender = row.get("gender", "").strip().upper()
                    class_name = row.get("class_name", "").strip()
                    guardian_phone = row.get("guardian_phone", "").strip()
                    status = row.get("status", "ACTIVE").strip().upper()

                    if not admission_number or not surname or not first_name:
                        error_rows.append(
                            f"Row {index}: admission_number, surname and first_name are required."
                        )
                        continue

                    school_class = SchoolClass.objects.filter(
                        school=school,
                        name__iexact=class_name,
                    ).first()

                    if not school_class:
                        error_rows.append(
                            f"Row {index}: class '{class_name}' not found."
                        )
                        continue

                    if gender not in [
                        StudentProfile.Gender.MALE,
                        StudentProfile.Gender.FEMALE,
                    ]:
                        error_rows.append(
                            f"Row {index}: invalid gender '{gender}'. Use MALE or FEMALE."
                        )
                        continue

                    if status not in [
                        StudentProfile.Status.ACTIVE,
                        StudentProfile.Status.INACTIVE,
                        StudentProfile.Status.GRADUATED,
                        StudentProfile.Status.TRANSFERRED,
                    ]:
                        status = StudentProfile.Status.ACTIVE

                    student, created = StudentProfile.objects.update_or_create(
                        school=school,
                        admission_number=admission_number,
                        defaults={
                            "surname": surname,
                            "first_name": first_name,
                            "middle_name": middle_name,
                            "gender": gender,
                            "current_class": school_class,
                            "guardian_phone": guardian_phone,
                            "status": status,
                        },
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                except Exception as e:
                    error_rows.append(f"Row {index}: {str(e)}")

            if created_count or updated_count:
                messages.success(
                    request,
                    f"Import completed. Created: {created_count}, Updated: {updated_count}."
                )

            if error_rows:
                request.session["student_import_errors"] = error_rows
                messages.warning(
                    request,
                    f"Import completed with {len(error_rows)} error(s)."
                )
                return redirect("student_import_errors")

            return redirect("data_tools_dashboard")

    else:
        form = StudentImportForm()

    return render(request, "data_tools/import_students.html", {
        "form": form,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def student_import_errors(request):
    errors = request.session.get("student_import_errors", [])

    return render(request, "data_tools/import_errors.html", {
        "errors": errors,
    })



@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def download_staff_import_template(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="staff_import_template.csv"'

    writer = csv.writer(response)

    writer.writerow([
        "staff_id",
        "surname",
        "first_name",
        "middle_name",
        "gender",
        "staff_type",
        "designation",
        "qualification",
        "phone",
        "status",
    ])

    writer.writerow([
        "STF001",
        "Abubakar",
        "Musa",
        "Ibrahim",
        "MALE",
        "TEACHING",
        "Mathematics Teacher",
        "B.Sc Mathematics",
        "08012345678",
        "ACTIVE",
    ])

    return response


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def export_staff_csv(request):
    school = request.user.school

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="staff_export.csv"'

    writer = csv.writer(response)

    writer.writerow([
        "staff_id",
        "surname",
        "first_name",
        "middle_name",
        "gender",
        "staff_type",
        "designation",
        "qualification",
        "phone",
        "status",
    ])

    staff_members = StaffProfile.objects.filter(
        school=school,
    ).select_related(
        "user",
    ).order_by(
        "user__last_name",
        "user__first_name",
    )

    for staff in staff_members:
        writer.writerow([
            staff.staff_id,
            staff.user.last_name if staff.user else "",
            staff.user.first_name if staff.user else "",
            "",
            staff.gender,
            staff.staff_type,
            staff.designation,
            staff.qualification,
            staff.phone,
            staff.status,
        ])

    return response


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def import_staff_csv(request):
    school = request.user.school

    if request.method == "POST":
        form = StaffImportForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = form.cleaned_data["file"]

            if not uploaded_file.name.endswith(".csv"):
                messages.error(request, "Only CSV files are supported for now.")
                return redirect("import_staff_csv")

            decoded_file = TextIOWrapper(
                uploaded_file.file,
                encoding="utf-8",
            )

            reader = csv.DictReader(decoded_file)

            created_count = 0
            updated_count = 0
            error_rows = []

            required_columns = [
                "staff_id",
                "surname",
                "first_name",
                "gender",
                "staff_type",
            ]

            missing_columns = [
                col for col in required_columns
                if col not in reader.fieldnames
            ]

            if missing_columns:
                messages.error(
                    request,
                    f"Missing required columns: {', '.join(missing_columns)}"
                )
                return redirect("import_staff_csv")

            for index, row in enumerate(reader, start=2):
                try:
                    staff_id = row.get("staff_id", "").strip()
                    surname = row.get("surname", "").strip()
                    first_name = row.get("first_name", "").strip()
                    middle_name = row.get("middle_name", "").strip()
                    gender = row.get("gender", "").strip().upper()
                    staff_type = row.get("staff_type", "").strip().upper()
                    designation = row.get("designation", "").strip()
                    qualification = row.get("qualification", "").strip()
                    phone = row.get("phone", "").strip()
                    status = row.get("status", "ACTIVE").strip().upper()

                    if not staff_id or not surname or not first_name:
                        error_rows.append(
                            f"Row {index}: staff_id, surname and first_name are required."
                        )
                        continue

                    if gender not in [
                        StaffProfile.Gender.MALE,
                        StaffProfile.Gender.FEMALE,
                    ]:
                        error_rows.append(
                            f"Row {index}: invalid gender '{gender}'. Use MALE or FEMALE."
                        )
                        continue

                    if staff_type not in [
                        StaffProfile.StaffType.TEACHING,
                        StaffProfile.StaffType.NON_TEACHING,
                    ]:
                        error_rows.append(
                            f"Row {index}: invalid staff_type '{staff_type}'. Use TEACHING or NON_TEACHING."
                        )
                        continue

                    if status not in [
                        StaffProfile.Status.ACTIVE,
                        StaffProfile.Status.INACTIVE,
                    ]:
                        status = StaffProfile.Status.ACTIVE

                    staff, created = StaffProfile.objects.update_or_create(
                        school=school,
                        staff_id=staff_id,
                        defaults={
                            "surname": surname,
                            "first_name": first_name,
                            "middle_name": middle_name,
                            "gender": gender,
                            "staff_type": staff_type,
                            "designation": designation,
                            "qualification": qualification,
                            "phone": phone,
                            "status": status,
                        },
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                except Exception as e:
                    error_rows.append(f"Row {index}: {str(e)}")

            if created_count or updated_count:
                messages.success(
                    request,
                    f"Staff import completed. Created: {created_count}, Updated: {updated_count}."
                )

            if error_rows:
                request.session["staff_import_errors"] = error_rows
                messages.warning(
                    request,
                    f"Import completed with {len(error_rows)} error(s)."
                )
                return redirect("staff_import_errors")

            return redirect("data_tools_dashboard")

    else:
        form = StaffImportForm()

    return render(request, "data_tools/import_staff.html", {
        "form": form,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def staff_import_errors(request):
    errors = request.session.get("staff_import_errors", [])

    return render(request, "data_tools/import_errors.html", {
        "errors": errors,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def download_parent_import_template(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="parent_import_template.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "surname",
        "first_name",
        "phone",
        "email",
        "address",
        "child_admission_number",
        "status",
    ])

    writer.writerow([
        "Muhammad",
        "Ibrahim",
        "08012345678",
        "parent@example.com",
        "Kano State",
        "ADM001",
        "ACTIVE",
    ])

    return response


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def export_parents_csv(request):
    school = request.user.school

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="parents_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "parent_name",
        "phone",
        "email",
        "children",
        "status",
    ])

    parents = ParentProfile.objects.filter(
        school=school,
    ).prefetch_related("children").select_related("user")

    for parent in parents:
        children = ", ".join([
            child.admission_number for child in parent.children.all()
        ])

        writer.writerow([
            parent.user.get_full_name() if parent.user else "",
            parent.phone,
            parent.user.email if parent.user else "",
            children,
            "ACTIVE" if parent.is_active else "INACTIVE",
        ])

    return response


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def import_parents_csv(request):
    school = request.user.school

    if request.method == "POST":
        form = ParentImportForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = form.cleaned_data["file"]

            if not uploaded_file.name.endswith(".csv"):
                messages.error(request, "Only CSV files are supported.")
                return redirect("import_parents_csv")

            decoded_file = TextIOWrapper(uploaded_file.file, encoding="utf-8")
            reader = csv.DictReader(decoded_file)

            created_count = 0
            updated_count = 0
            error_rows = []

            required_columns = [
                "surname",
                "first_name",
                "phone",
                "child_admission_number",
            ]

            missing_columns = [
                col for col in required_columns
                if col not in reader.fieldnames
            ]

            if missing_columns:
                messages.error(request, f"Missing required columns: {', '.join(missing_columns)}")
                return redirect("import_parents_csv")

            for index, row in enumerate(reader, start=2):
                try:
                    surname = row.get("surname", "").strip()
                    first_name = row.get("first_name", "").strip()
                    phone = row.get("phone", "").strip()
                    email = row.get("email", "").strip()
                    address = row.get("address", "").strip()
                    child_admission_number = row.get("child_admission_number", "").strip()
                    status = row.get("status", "ACTIVE").strip().upper()

                    if not surname or not first_name or not phone:
                        error_rows.append(f"Row {index}: surname, first_name and phone are required.")
                        continue

                    child = StudentProfile.objects.filter(
                        school=school,
                        admission_number=child_admission_number,
                    ).first()

                    if not child:
                        error_rows.append(
                            f"Row {index}: child admission number '{child_admission_number}' not found."
                        )
                        continue

                    username = f"parent_{phone}".replace(" ", "")

                    user, _ = User.objects.get_or_create(
                        username=username,
                        defaults={
                            "first_name": first_name,
                            "last_name": surname,
                            "email": email,
                            "school": school,
                            "role": User.Role.PARENT,
                        },
                    )

                    user.first_name = first_name
                    user.last_name = surname
                    user.email = email
                    user.school = school
                    user.role = User.Role.PARENT
                    user.save()

                    parent, created = ParentProfile.objects.update_or_create(
                        school=school,
                        phone=phone,
                        defaults={
                            "user": user,
                            "address": address,
                            "is_active": status == "ACTIVE",
                        },
                    )

                    parent.children.add(child)

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                except Exception as e:
                    error_rows.append(f"Row {index}: {str(e)}")

            if created_count or updated_count:
                messages.success(
                    request,
                    f"Parent import completed. Created: {created_count}, Updated: {updated_count}."
                )

            if error_rows:
                request.session["parent_import_errors"] = error_rows
                messages.warning(request, f"Import completed with {len(error_rows)} error(s).")
                return redirect("parent_import_errors")

            return redirect("data_tools_dashboard")

    else:
        form = ParentImportForm()

    return render(request, "data_tools/import_parents.html", {
        "form": form,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def parent_import_errors(request):
    errors = request.session.get("parent_import_errors", [])

    return render(request, "data_tools/import_errors.html", {
        "errors": errors,
    })




@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def download_cbt_question_template(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="cbt_questions_template.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "class_name",
        "subject_name",
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_option",
        "difficulty_level",
        "explanation",
        "is_active",
    ])

    writer.writerow([
        "SSS 1",
        "Mathematics",
        "What is 2 + 2?",
        "2",
        "3",
        "4",
        "5",
        "C",
        "EASY",
        "2 + 2 = 4",
        "TRUE",
    ])

    return response


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def export_cbt_questions_csv(request):
    school = request.user.school

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="cbt_questions_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "class_name",
        "subject_name",
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_option",
        "difficulty_level",
        "explanation",
        "is_active",
    ])

    questions = CBTQuestion.objects.filter(
        school=school,
    ).select_related(
        "school_class",
        "subject",
    ).order_by("-created_at")

    for q in questions:
        writer.writerow([
            q.school_class.name if q.school_class else "",
            q.subject.name if q.subject else "",
            q.question_text,
            q.option_a,
            q.option_b,
            q.option_c,
            q.option_d,
            q.correct_option,
            q.difficulty_level,
            q.explanation,
            "TRUE" if q.is_active else "FALSE",
        ])

    return response


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def import_cbt_questions_csv(request):
    school = request.user.school

    if request.method == "POST":
        form = CBTQuestionImportForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = form.cleaned_data["file"]

            if not uploaded_file.name.endswith(".csv"):
                messages.error(request, "Only CSV files are supported.")
                return redirect("import_cbt_questions_csv")

            decoded_file = TextIOWrapper(uploaded_file.file, encoding="utf-8")
            reader = csv.DictReader(decoded_file)

            created_count = 0
            error_rows = []

            required_columns = [
                "class_name",
                "subject_name",
                "question_text",
                "option_a",
                "option_b",
                "option_c",
                "option_d",
                "correct_option",
            ]

            missing_columns = [
                col for col in required_columns
                if col not in reader.fieldnames
            ]

            if missing_columns:
                messages.error(request, f"Missing required columns: {', '.join(missing_columns)}")
                return redirect("import_cbt_questions_csv")

            for index, row in enumerate(reader, start=2):
                try:
                    class_name = row.get("class_name", "").strip()
                    subject_name = row.get("subject_name", "").strip()
                    question_text = row.get("question_text", "").strip()
                    option_a = row.get("option_a", "").strip()
                    option_b = row.get("option_b", "").strip()
                    option_c = row.get("option_c", "").strip()
                    option_d = row.get("option_d", "").strip()
                    correct_option = row.get("correct_option", "").strip().upper()
                    difficulty_level = row.get("difficulty_level", "MEDIUM").strip().upper()
                    explanation = row.get("explanation", "").strip()
                    is_active = row.get("is_active", "TRUE").strip().upper() in ["TRUE", "YES", "1"]

                    school_class = SchoolClass.objects.filter(
                        school=school,
                        name__iexact=class_name,
                    ).first()

                    subject = Subject.objects.filter(
                        school=school,
                        name__iexact=subject_name,
                    ).first()

                    if not school_class:
                        error_rows.append(f"Row {index}: class '{class_name}' not found.")
                        continue

                    if not subject:
                        error_rows.append(f"Row {index}: subject '{subject_name}' not found.")
                        continue

                    if correct_option not in ["A", "B", "C", "D"]:
                        error_rows.append(f"Row {index}: correct_option must be A, B, C or D.")
                        continue

                    if difficulty_level not in ["EASY", "MEDIUM", "HARD"]:
                        difficulty_level = "MEDIUM"

                    CBTQuestion.objects.create(
                        school=school,
                        school_class=school_class,
                        subject=subject,
                        question_text=question_text,
                        option_a=option_a,
                        option_b=option_b,
                        option_c=option_c,
                        option_d=option_d,
                        correct_option=correct_option,
                        difficulty_level=difficulty_level,
                        explanation=explanation,
                        is_active=is_active,
                        created_by=request.user,
                    )

                    created_count += 1

                except Exception as e:
                    error_rows.append(f"Row {index}: {str(e)}")

            if created_count:
                messages.success(request, f"CBT questions imported successfully. Created: {created_count}.")

            if error_rows:
                request.session["cbt_import_errors"] = error_rows
                messages.warning(request, f"Import completed with {len(error_rows)} error(s).")
                return redirect("cbt_import_errors")

            return redirect("data_tools_dashboard")

    else:
        form = CBTQuestionImportForm()

    return render(request, "data_tools/import_cbt_questions.html", {
        "form": form,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def cbt_import_errors(request):
    errors = request.session.get("cbt_import_errors", [])

    return render(request, "data_tools/import_errors.html", {
        "errors": errors,
    })



@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def export_results_csv(request):
    school = request.user.school

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="results_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "student",
        "admission_number",
        "class",
        "session",
        "term",
        "subject",
        "ca_score",
        "exam_score",
        "total_score",
        "grade",
        "remark",
        "published",
    ])

    results = ResultEntry.objects.filter(
        school=school,
    ).select_related(
        "student",
        "school_class",
        "session",
        "term",
        "subject",
    )

    for r in results:
        writer.writerow([
            r.student.full_name,
            r.student.admission_number,
            r.school_class.name,
            r.session.name,
            r.term.name,
            r.subject.name,
            r.ca_score,
            r.exam_score,
            r.total_score,
            r.grade,
            r.remark,
            "TRUE" if r.is_published else "FALSE",
        ])

    return response




@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def export_invoices_csv(request):
    school = request.user.school

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="invoices_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "invoice_id",
        "student",
        "admission_number",
        "class",
        "total_amount",
        "amount_paid",
        "balance",
        "status",
        "generated_at",
    ])

    invoices = StudentInvoice.objects.filter(
        school=school,
    ).select_related(
        "student",
        "student__current_class",
    )

    for invoice in invoices:
        writer.writerow([
            invoice.id,
            invoice.student.full_name,
            invoice.student.admission_number,
            invoice.student.current_class.name if invoice.student.current_class else "",
            invoice.total_amount,
            invoice.amount_paid,
            invoice.balance,
            invoice.status,
            invoice.generated_at,
        ])

    return response



