from decimal import Decimal

from django.db.models import Avg, Sum

from apps.attendance.models import StudentAttendance
from apps.cbt.models import CBTAttempt
from apps.finance.models import StudentInvoice
from apps.results.models import ResultEntry


def get_student_intelligence(student):
    school = student.school

    results = ResultEntry.objects.filter(
        school=school,
        student=student,
        is_published=True,
    ).select_related("subject")

    average_score = results.aggregate(
        avg=Avg("total_score")
    )["avg"] or 0

    weak_subjects = results.filter(
        total_score__lt=50
    ).select_related("subject")[:5]

    strong_subjects = results.filter(
        total_score__gte=70
    ).select_related("subject")[:5]

    attendance_records = StudentAttendance.objects.filter(
        school=school,
        student=student,
    )

    total_attendance = attendance_records.count()

    present_count = attendance_records.filter(
        status=StudentAttendance.Status.PRESENT,
    ).count()

    attendance_percentage = 0

    if total_attendance > 0:
        attendance_percentage = round(
            (present_count / total_attendance) * 100,
            1,
        )

    cbt_average = CBTAttempt.objects.filter(
        school=school,
        student=student,
        status=CBTAttempt.Status.SUBMITTED,
    ).aggregate(
        avg=Avg("percentage")
    )["avg"] or 0

    fee_balance = StudentInvoice.objects.filter(
        school=school,
        student=student,
    ).aggregate(
        total=Sum("balance")
    )["total"] or Decimal("0.00")

    risk_points = 0
    recommendations = []

    if average_score < 50:
        risk_points += 3
        recommendations.append(
            "Academic performance is below average. Extra coaching and close monitoring are recommended."
        )
    elif average_score < 60:
        risk_points += 2
        recommendations.append(
            "Academic performance is fair but needs improvement in weaker subjects."
        )
    else:
        recommendations.append(
            "Academic performance is stable. Continue regular study and revision."
        )

    if attendance_percentage < 75:
        risk_points += 3
        recommendations.append(
            "Attendance is low. The student should improve school attendance immediately."
        )
    elif attendance_percentage < 90:
        risk_points += 1
        recommendations.append(
            "Attendance is acceptable but can still improve."
        )

    if cbt_average and cbt_average < 50:
        risk_points += 2
        recommendations.append(
            "CBT performance is weak. More practice tests are recommended."
        )

    if fee_balance and fee_balance > 0:
        risk_points += 1
        recommendations.append(
            "There is an outstanding fee balance that may affect access to some services."
        )

    if risk_points >= 6:
        risk_level = "HIGH"
        risk_label = "High Risk"
    elif risk_points >= 3:
        risk_level = "MEDIUM"
        risk_label = "Medium Risk"
    else:
        risk_level = "LOW"
        risk_label = "Low Risk"

    return {
        "average_score": round(average_score, 1),
        "attendance_percentage": attendance_percentage,
        "cbt_average": round(cbt_average, 1),
        "fee_balance": fee_balance,
        "weak_subjects": weak_subjects,
        "strong_subjects": strong_subjects,
        "risk_level": risk_level,
        "risk_label": risk_label,
        "recommendations": recommendations,
    }


def calculate_student_risk_score(student):
    insight = get_student_intelligence(student)

    score = 0

    if insight["average_score"] < 40:
        score += 35
    elif insight["average_score"] < 50:
        score += 25
    elif insight["average_score"] < 60:
        score += 15

    if insight["attendance_percentage"] < 60:
        score += 30
    elif insight["attendance_percentage"] < 75:
        score += 20
    elif insight["attendance_percentage"] < 90:
        score += 10

    if insight["cbt_average"] and insight["cbt_average"] < 40:
        score += 20
    elif insight["cbt_average"] and insight["cbt_average"] < 50:
        score += 15

    if insight["fee_balance"] and insight["fee_balance"] > 0:
        score += 10

    if score >= 70:
        level = "CRITICAL"
        label = "Critical Risk"
    elif score >= 50:
        level = "HIGH"
        label = "High Risk"
    elif score >= 30:
        level = "MEDIUM"
        label = "Medium Risk"
    else:
        level = "LOW"
        label = "Low Risk"

    return {
        "score": min(score, 100),
        "level": level,
        "label": label,
        "insight": insight,
    }


def get_school_risk_students(school, limit=50):
    from apps.students.models import StudentProfile

    students = StudentProfile.objects.filter(
        school=school,
        status=StudentProfile.Status.ACTIVE,
    ).select_related(
        "user",
        "current_class",
    )

    risk_rows = []

    for student in students:
        risk = calculate_student_risk_score(student)

        risk_rows.append({
            "student": student,
            "risk_score": risk["score"],
            "risk_level": risk["level"],
            "risk_label": risk["label"],
            "average_score": risk["insight"]["average_score"],
            "attendance_percentage": risk["insight"]["attendance_percentage"],
            "cbt_average": risk["insight"]["cbt_average"],
            "fee_balance": risk["insight"]["fee_balance"],
        })

    risk_rows.sort(key=lambda x: x["risk_score"], reverse=True)

    return risk_rows[:limit]