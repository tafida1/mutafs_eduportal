from apps.attendance.models import StudentAttendance


def get_student_attendance_summary(
    *,
    school,
    student,
    session=None,
    term=None,
):
    queryset = StudentAttendance.objects.filter(
        school=school,
        student=student,
    )

    if session:
        queryset = queryset.filter(session=session)

    if term:
        queryset = queryset.filter(term=term)

    total_days = queryset.count()

    present_days = queryset.filter(
        status=StudentAttendance.Status.PRESENT
    ).count()

    absent_days = queryset.filter(
        status=StudentAttendance.Status.ABSENT
    ).count()

    late_days = queryset.filter(
        status=StudentAttendance.Status.LATE
    ).count()

    excused_days = queryset.filter(
        status=StudentAttendance.Status.EXCUSED
    ).count()

    attendance_percentage = 0

    if total_days > 0:
        attendance_percentage = round(
            (present_days / total_days) * 100,
            2,
        )

    if attendance_percentage >= 90:
        attendance_remark = "Excellent Attendance"
    elif attendance_percentage >= 75:
        attendance_remark = "Very Regular"
    elif attendance_percentage >= 60:
        attendance_remark = "Average Attendance"
    elif attendance_percentage >= 40:
        attendance_remark = "Poor Attendance"
    else:
        attendance_remark = "Chronic Absenteeism"

    return {
        "total_days": total_days,
        "present_days": present_days,
        "absent_days": absent_days,
        "late_days": late_days,
        "excused_days": excused_days,
        "attendance_percentage": attendance_percentage,
        "attendance_remark": attendance_remark,
    }