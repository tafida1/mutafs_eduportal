from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from apps.staffs.models import StaffProfile
from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.schools.models import School
from apps.students.models import StudentProfile


@login_required
def dashboard_router(request):
    user = request.user

    if user.is_super_admin:
        return redirect("super_admin_dashboard")

    if user.is_school_admin:
        return redirect("school_admin_dashboard")

    if user.is_teacher:
        return redirect("teacher_dashboard")

    if user.is_student:
        return redirect("student_dashboard")

    if user.is_parent:
        return redirect("parent_dashboard")

    return render(request, "dashboard/unknown_role.html")


@login_required
def super_admin_dashboard(request):
    from django.db.models import Sum, Avg
    from django.utils import timezone

    from apps.accounts.models import User
    from apps.audit.models import AuditLog
    from apps.cbt.models import CBTAttempt, CBTExam
    from apps.finance.models import StudentInvoice
    from apps.results.models import ResultEntry
    from apps.schools.models import School, SchoolSubscription, SubscriptionPayment
    from apps.staffs.models import StaffProfile
    from apps.students.models import StudentProfile
    from apps.parents.models import ParentProfile

    today = timezone.localdate()

    schools = School.objects.all()
    users = User.objects.all()
    subscriptions = SchoolSubscription.objects.select_related("school", "plan")
    subscription_payments = SubscriptionPayment.objects.all()

    context = {
        "total_schools": schools.count(),
        "active_schools": schools.filter(is_active=True).count(),
        "disabled_schools": schools.filter(is_active=False).count(),

        "trial_schools": subscriptions.filter(status=SchoolSubscription.Status.TRIAL).count(),
        "active_subscriptions": subscriptions.filter(status=SchoolSubscription.Status.ACTIVE).count(),
        "expired_subscriptions": subscriptions.filter(status=SchoolSubscription.Status.EXPIRED).count(),
        "suspended_subscriptions": subscriptions.filter(status=SchoolSubscription.Status.SUSPENDED).count(),

        "total_users": users.count(),
        "school_admins": users.filter(role=User.Role.SCHOOL_ADMIN).count(),
        "teachers": users.filter(role=User.Role.TEACHER).count(),
        "students": users.filter(role=User.Role.STUDENT).count(),
        "parents": users.filter(role=User.Role.PARENT).count(),

        "student_profiles": StudentProfile.objects.count(),
        "staff_profiles": StaffProfile.objects.count(),
        "parent_profiles": ParentProfile.objects.count(),

        "subscription_revenue": subscription_payments.aggregate(
            total=Sum("amount")
        )["total"] or 0,

        "school_fee_volume": StudentInvoice.objects.aggregate(
            total=Sum("total_amount")
        )["total"] or 0,

        "school_fee_paid": StudentInvoice.objects.aggregate(
            total=Sum("amount_paid")
        )["total"] or 0,

        "school_fee_balance": StudentInvoice.objects.aggregate(
            total=Sum("balance")
        )["total"] or 0,

        "cbt_exams": CBTExam.objects.count(),
        "cbt_attempts": CBTAttempt.objects.count(),
        "cbt_average": CBTAttempt.objects.filter(
            status=CBTAttempt.Status.SUBMITTED
        ).aggregate(avg=Avg("percentage"))["avg"] or 0,

        "result_entries": ResultEntry.objects.count(),
        "published_results": ResultEntry.objects.filter(is_published=True).count(),

        "audit_logs": AuditLog.objects.count(),
        "security_events": AuditLog.objects.filter(
            action=AuditLog.Action.SECURITY_BLOCK
        ).count(),

        "recent_schools": schools.order_by("-created_at")[:6],
        "recent_subscriptions": subscriptions.order_by("end_date")[:8],
        "recent_audit_logs": AuditLog.objects.select_related(
            "actor",
            "school",
        ).order_by("-created_at")[:8],

        "today": today,
    }

    return render(request, "dashboard/super_admin.html", context)

    


@login_required
def school_admin_dashboard(request):
    from django.db.models import Sum, Avg
    from django.utils import timezone

    from apps.academics.models import AcademicSession, AcademicTerm, SchoolClass, Subject
    from apps.attendance.models import StudentAttendance, StaffAttendance
    from apps.cbt.models import CBTAttempt, CBTExam
    from apps.finance.models import StudentInvoice
    from apps.lessons.models import LessonResource
    from apps.notifications.models import Announcement
    from apps.parents.models import ParentProfile
    from apps.results.models import ResultEntry
    from apps.staffs.models import StaffProfile
    from apps.students.models import StudentProfile
    from django.conf import settings
    from apps.core.cache_utils import tenant_cache_key, get_cached_or_set

    school = request.user.school
    today = timezone.localdate()

    students = StudentProfile.objects.filter(school=school)
    staff = StaffProfile.objects.filter(school=school)
    invoices = StudentInvoice.objects.filter(school=school)
    cbt_attempts = CBTAttempt.objects.filter(school=school, status=CBTAttempt.Status.SUBMITTED)

    finance_stats = get_cached_or_set(
        tenant_cache_key(school.id, "finance_stats"),
        lambda: {
            "total_billed": invoices.aggregate(total=Sum("total_amount"))["total"] or 0,
            "total_paid": invoices.aggregate(total=Sum("amount_paid"))["total"] or 0,
            "total_balance": invoices.aggregate(total=Sum("balance"))["total"] or 0,
        },
        timeout=getattr(settings, "CACHE_TTL", 300),
    )

    total_billed = finance_stats["total_billed"]
    total_paid = finance_stats["total_paid"]
    total_balance = finance_stats["total_balance"]

    student_present_today = StudentAttendance.objects.filter(
        school=school,
        date=today,
        status=StudentAttendance.Status.PRESENT,
    ).count()

    student_absent_today = StudentAttendance.objects.filter(
        school=school,
        date=today,
        status=StudentAttendance.Status.ABSENT,
    ).count()

    staff_present_today = StaffAttendance.objects.filter(
        school=school,
        date=today,
        status=StaffAttendance.Status.PRESENT,
    ).count()

    staff_absent_today = StaffAttendance.objects.filter(
        school=school,
        date=today,
        status=StaffAttendance.Status.ABSENT,
    ).count()

    class_distribution = SchoolClass.objects.filter(
        school=school
    ).order_by("position_order", "name")

    class_cards = []

    for school_class in class_distribution:
        class_cards.append({
            "class": school_class,
            "students_count": students.filter(current_class=school_class).count(),
        })

    recent_results = ResultEntry.objects.filter(
        school=school,
    ).select_related(
        "student",
        "subject",
        "school_class",
    ).order_by("-updated_at")[:6]

    recent_resources = LessonResource.objects.filter(
        school=school,
        is_published=True,
    ).select_related("subject", "school_class").order_by("-created_at")[:5]

    recent_announcements = Announcement.objects.filter(
        school=school,
        is_active=True,
    ).order_by("-created_at")[:5]

    context = {
        "current_session": AcademicSession.objects.filter(school=school, is_current=True).first(),
        "current_term": AcademicTerm.objects.filter(school=school, is_current=True).first(),

        "students_count": students.count(),
        "active_students_count": students.filter(status=StudentProfile.Status.ACTIVE).count(),
        "parents_count": ParentProfile.objects.filter(school=school).count(),
        "staffs_count": staff.count(),
        "teachers_count": staff.filter(staff_type=StaffProfile.StaffType.TEACHING).count(),

        "classes_count": SchoolClass.objects.filter(school=school).count(),
        "subjects_count": Subject.objects.filter(school=school).count(),

        "student_present_today": student_present_today,
        "student_absent_today": student_absent_today,
        "staff_present_today": staff_present_today,
        "staff_absent_today": staff_absent_today,

        "total_billed": total_billed,
        "total_paid": total_paid,
        "total_balance": total_balance,

        "cbt_exams_count": CBTExam.objects.filter(school=school).count(),
        "cbt_attempts_count": cbt_attempts.count(),
        "cbt_average": cbt_attempts.aggregate(avg=Avg("percentage"))["avg"] or 0,

        "result_entries_count": ResultEntry.objects.filter(school=school).count(),
        "published_results_count": ResultEntry.objects.filter(
            school=school,
            is_published=True,
        ).count(),

        "class_cards": class_cards,
        "recent_results": recent_results,
        "recent_resources": recent_resources,
        "recent_announcements": recent_announcements,
    }

    return render(request, "dashboard/school_admin.html", context)




@login_required
def teacher_dashboard(request):
    return redirect("teacher_workspace")


@login_required
def student_dashboard(request):
    from datetime import datetime
    from django.db.models import Avg, Sum
    from django.shortcuts import get_object_or_404

    from apps.academics.models import AcademicSession, AcademicTerm, Subject
    from apps.attendance.models import StudentAttendance
    from apps.cbt.models import CBTAttempt
    from apps.finance.models import StudentInvoice
    from apps.lessons.models import LessonResource
    from apps.notifications.models import UserNotification
    from apps.timetable.models import TimetableEntry

    school = request.user.school

    student = get_object_or_404(
        StudentProfile.objects.select_related(
            "user",
            "current_class",
            "school",
        ),
        user=request.user,
        school=school,
    )

    current_session = AcademicSession.objects.filter(
        school=school,
        is_current=True,
    ).first()

    current_term = AcademicTerm.objects.filter(
        school=school,
        is_current=True,
    ).first()

    attendance_records = StudentAttendance.objects.filter(
        school=school,
        student=student,
    )

    total_attendance = attendance_records.count()

    present_attendance = attendance_records.filter(
        status=StudentAttendance.Status.PRESENT,
    ).count()

    attendance_percentage = 0

    if total_attendance > 0:
        attendance_percentage = round(
            (present_attendance / total_attendance) * 100,
            1,
        )

    total_subjects = Subject.objects.filter(
        school=school,
        is_active=True,
    ).count()

    cbt_attempts = CBTAttempt.objects.filter(
        school=school,
        student=student,
        status=CBTAttempt.Status.SUBMITTED,
    )

    average_cbt_score = cbt_attempts.aggregate(
        avg=Avg("percentage")
    )["avg"] or 0

    outstanding_fees = StudentInvoice.objects.filter(
        school=school,
        student=student,
    ).aggregate(
        total=Sum("balance")
    )["total"] or 0

    recent_notifications = UserNotification.objects.filter(
        user=request.user,
        announcement__is_active=True,
    ).select_related("announcement").order_by("-created_at")[:5]

    recent_resources = LessonResource.objects.filter(
        school=school,
        is_published=True,
    ).select_related("subject").order_by("-created_at")[:5]

    today_day = datetime.now().strftime("%A").upper()

    today_timetable = TimetableEntry.objects.filter(
        school=school,
        school_class=student.current_class,
        time_slot__day=today_day,
        is_active=True,
    ).select_related(
        "subject",
        "time_slot",
    ).order_by("time_slot__start_time")

    context = {
        "student": student,
        "current_session": current_session,
        "current_term": current_term,
        "attendance_percentage": attendance_percentage,
        "total_subjects": total_subjects,
        "average_cbt_score": round(average_cbt_score, 1),
        "outstanding_fees": outstanding_fees,
        "recent_notifications": recent_notifications,
        "recent_resources": recent_resources,
        "today_timetable": today_timetable,
    }

    return render(request, "dashboard/student.html", context)


@login_required
def parent_dashboard(request):
    return redirect("parent_portal_dashboard")



from django.shortcuts import render


def custom_404(request, exception):
    return render(request, "errors/404.html", status=404)


def custom_500(request):
    return render(request, "errors/500.html", status=500)


def custom_403(request, exception):
    return render(request, "errors/403.html", status=403)



def public_about(request):
    return render(request, "public_pages/about.html")


def public_contact(request):
    return render(request, "public_pages/contact.html")


def public_mission_vision(request):
    return render(request, "public_pages/mission_vision.html")