from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.models import User
from apps.academics.models import SchoolClass, Subject
from apps.attendance.models import StudentAttendance, StaffAttendance
from apps.cbt.models import CBTAttempt
from apps.core.decorators import role_required
from apps.finance.models import StudentInvoice
from apps.results.models import ResultEntry
from apps.staffs.models import StaffProfile
from apps.students.models import StudentProfile


def current_school(request):
    return request.user.school


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def analytics_dashboard(request):
    school = current_school(request)
    today = timezone.localdate()

    students = StudentProfile.objects.filter(school=school)
    staff = StaffProfile.objects.filter(school=school)
    invoices = StudentInvoice.objects.filter(school=school)
    results = ResultEntry.objects.filter(school=school)
    cbt_attempts = CBTAttempt.objects.filter(school=school)

    context = {
        "total_students": students.count(),
        "active_students": students.filter(status=StudentProfile.Status.ACTIVE).count(),
        "male_students": students.filter(gender=StudentProfile.Gender.MALE).count(),
        "female_students": students.filter(gender=StudentProfile.Gender.FEMALE).count(),

        "total_staff": staff.count(),
        "teachers_count": staff.filter(staff_type=StaffProfile.StaffType.TEACHING).count(),
        "non_teaching_count": staff.filter(staff_type=StaffProfile.StaffType.NON_TEACHING).count(),

        "classes_count": SchoolClass.objects.filter(school=school).count(),
        "subjects_count": Subject.objects.filter(school=school).count(),

        "student_present_today": StudentAttendance.objects.filter(
            school=school,
            date=today,
            status=StudentAttendance.Status.PRESENT,
        ).count(),
        "student_absent_today": StudentAttendance.objects.filter(
            school=school,
            date=today,
            status=StudentAttendance.Status.ABSENT,
        ).count(),
        "staff_present_today": StaffAttendance.objects.filter(
            school=school,
            date=today,
            status=StaffAttendance.Status.PRESENT,
        ).count(),
        "staff_absent_today": StaffAttendance.objects.filter(
            school=school,
            date=today,
            status=StaffAttendance.Status.ABSENT,
        ).count(),

        "result_entries": results.count(),
        "published_results": results.filter(is_published=True).count(),
        "average_result_score": results.aggregate(avg=Avg("total_score"))["avg"] or 0,

        "total_billed": invoices.aggregate(total=Sum("total_amount"))["total"] or 0,
        "total_paid": invoices.aggregate(total=Sum("amount_paid"))["total"] or 0,
        "total_balance": invoices.aggregate(total=Sum("balance"))["total"] or 0,
        "paid_invoices": invoices.filter(status=StudentInvoice.Status.PAID).count(),
        "unpaid_invoices": invoices.filter(status=StudentInvoice.Status.UNPAID).count(),

        "cbt_attempts": cbt_attempts.count(),
        "cbt_average_score": cbt_attempts.aggregate(avg=Avg("percentage"))["avg"] or 0,

        "students_by_class": students.values(
            "current_class__name"
        ).annotate(
            total=Count("id")
        ).order_by("current_class__position_order"),

        "finance_by_status": invoices.values(
            "status"
        ).annotate(
            total=Count("id"),
            amount=Sum("balance"),
        ),
    }

    return render(request, "analytics/dashboard.html", context)



@login_required
@role_required(User.Role.SUPER_ADMIN)
def global_analytics_dashboard(request):
    from apps.schools.models import School, SchoolSubscription, SubscriptionPayment
    from apps.accounts.models import User
    from apps.students.models import StudentProfile
    from apps.staffs.models import StaffProfile
    from apps.parents.models import ParentProfile
    from apps.finance.models import StudentInvoice
    from apps.cbt.models import CBTAttempt
    from apps.results.models import ResultEntry
    from apps.audit.models import AuditLog

    schools = School.objects.all()
    users = User.objects.all()
    subscriptions = SchoolSubscription.objects.select_related("school", "plan")
    invoices = StudentInvoice.objects.all()

    context = {
        "total_schools": schools.count(),
        "active_schools": schools.filter(is_active=True).count(),
        "disabled_schools": schools.filter(is_active=False).count(),

        "trial_schools": subscriptions.filter(status=SchoolSubscription.Status.TRIAL).count(),
        "active_subscriptions": subscriptions.filter(status=SchoolSubscription.Status.ACTIVE).count(),
        "expired_subscriptions": subscriptions.filter(status=SchoolSubscription.Status.EXPIRED).count(),
        "suspended_subscriptions": subscriptions.filter(status=SchoolSubscription.Status.SUSPENDED).count(),

        "total_users": users.count(),
        "super_admins": users.filter(role=User.Role.SUPER_ADMIN).count(),
        "school_admins": users.filter(role=User.Role.SCHOOL_ADMIN).count(),
        "teachers": users.filter(role=User.Role.TEACHER).count(),
        "students": users.filter(role=User.Role.STUDENT).count(),
        "parents": users.filter(role=User.Role.PARENT).count(),

        "total_student_profiles": StudentProfile.objects.count(),
        "total_staff_profiles": StaffProfile.objects.count(),
        "total_parent_profiles": ParentProfile.objects.count(),

        "subscription_revenue": SubscriptionPayment.objects.aggregate(
            total=Sum("amount")
        )["total"] or 0,

        "school_fees_billed": invoices.aggregate(
            total=Sum("total_amount")
        )["total"] or 0,

        "school_fees_paid": invoices.aggregate(
            total=Sum("amount_paid")
        )["total"] or 0,

        "school_fees_outstanding": invoices.aggregate(
            total=Sum("balance")
        )["total"] or 0,

        "cbt_attempts": CBTAttempt.objects.count(),
        "cbt_average": CBTAttempt.objects.aggregate(
            avg=Avg("percentage")
        )["avg"] or 0,

        "result_entries": ResultEntry.objects.count(),
        "published_result_entries": ResultEntry.objects.filter(is_published=True).count(),

        "audit_logs": AuditLog.objects.count(),
        "security_events": AuditLog.objects.filter(
            action=AuditLog.Action.SECURITY_BLOCK
        ).count(),

        "recent_schools": schools.order_by("-created_at")[:8],
        "recent_subscriptions": subscriptions.order_by("end_date")[:8],
    }

    return render(request, "analytics/global_dashboard.html", context)