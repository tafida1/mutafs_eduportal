from decimal import Decimal

from django.db.models import Avg, Sum

from .models import ResultEntry


def get_academic_remark(average):
    average = Decimal(average or 0)

    if average >= 75:
        return ResultEntry.AcademicRemark.EXCELLENT, "Excellent performance. Keep up the outstanding work."
    if average >= 65:
        return ResultEntry.AcademicRemark.VERY_GOOD, "Very good performance. More effort can lead to excellence."
    if average >= 50:
        return ResultEntry.AcademicRemark.GOOD, "Good performance. Maintain steady improvement."
    if average >= 45:
        return ResultEntry.AcademicRemark.FAIR, "Fair performance. More concentration is needed."
    if average >= 40:
        return ResultEntry.AcademicRemark.POOR, "Weak performance. Serious improvement is required."
    return ResultEntry.AcademicRemark.CRITICAL, "Critical performance. Urgent academic attention is required."


def get_promotion_status(average, failed_subjects):
    average = Decimal(average or 0)

    if average >= 50 and failed_subjects <= 2:
        return ResultEntry.PromotionStatus.PROMOTED

    if average >= 45 and failed_subjects <= 3:
        return ResultEntry.PromotionStatus.PROBATION

    return ResultEntry.PromotionStatus.REPEATED


def get_teacher_comment(average, failed_subjects):
    average = Decimal(average or 0)

    if average >= 75:
        return "Excellent academic performance. The student should maintain this outstanding effort."
    if average >= 65:
        return "Very good performance. The student is encouraged to work harder for excellence."
    if average >= 50:
        return "Good performance. The student should remain focused and improve further."
    if average >= 45:
        return "Fair performance. The student needs more concentration and regular study."
    if average >= 40:
        return "Weak performance. The student requires close monitoring and academic support."
    return "Poor performance. Serious academic attention and guidance are urgently required."


def get_principal_comment(average, failed_subjects):
    average = Decimal(average or 0)

    if average >= 75:
        return "Excellent result. Promoted with commendation."
    if average >= 65:
        return "Very good result. Promoted."
    if average >= 50:
        return "Good result. Promoted."
    if average >= 45:
        return "Fair result. Promoted on probation."
    if average >= 40:
        return "Result is weak. Promoted on strict probation."
    return "Result is poor. Student is advised to repeat for better foundation."


def recompute_class_result_intelligence(*, school, session, term, school_class):
    entries = ResultEntry.objects.filter(
        school=school,
        session=session,
        term=term,
        school_class=school_class,
    ).select_related("student", "subject")

    student_ids = entries.values_list("student_id", flat=True).distinct()

    student_summaries = []

    for student_id in student_ids:
        student_entries = entries.filter(student_id=student_id)

        total = student_entries.aggregate(total=Sum("total_score"))["total"] or Decimal("0")
        average = student_entries.aggregate(avg=Avg("total_score"))["avg"] or Decimal("0")

        failed_subjects = student_entries.filter(total_score__lt=40).count()

        student_summaries.append({
            "student_id": student_id,
            "total": total,
            "average": average,
            "failed_subjects": failed_subjects,
        })

    student_summaries.sort(key=lambda item: item["total"], reverse=True)

    for index, item in enumerate(student_summaries, start=1):
        remark, comment = get_academic_remark(item["average"])
        promotion_status = get_promotion_status(
            item["average"],
            item["failed_subjects"],
        )

        teacher_comment = get_teacher_comment(
            item["average"],
            item["failed_subjects"],
        )

        principal_comment = get_principal_comment(
            item["average"],
            item["failed_subjects"],
        )

        entries.filter(student_id=item["student_id"]).update(
            class_position=index,
            academic_remark=remark,
            auto_comment=comment,
            promotion_status=promotion_status,
            teacher_comment=teacher_comment,
            principal_comment=principal_comment,
        )

    subjects = entries.values_list("subject_id", flat=True).distinct()

    for subject_id in subjects:
        subject_entries = list(
            entries.filter(subject_id=subject_id).order_by("-total_score")
        )

        for index, entry in enumerate(subject_entries, start=1):
            entry.subject_position = index
            entry.save(update_fields=["subject_position"])
