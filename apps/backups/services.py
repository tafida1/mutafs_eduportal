import csv
from pathlib import Path
from django.conf import settings
from django.utils import timezone

from apps.students.models import StudentProfile
from apps.staffs.models import StaffProfile
from apps.parents.models import ParentProfile
from apps.finance.models import StudentInvoice
from apps.results.models import ResultEntry
from .models import BackupLog


def export_school_data_csv(*, school, user=None):
    export_dir = Path(settings.BASE_DIR) / "backups" / "exports" / f"school_{school.id}"
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")

    files = []

    datasets = [
        (
            "students",
            StudentProfile.objects.filter(school=school),
            ["id", "admission_number", "surname", "first_name", "middle_name", "gender", "status"],
        ),
        (
            "staff",
            StaffProfile.objects.filter(school=school),
            ["id", "staff_id", "staff_type", "designation", "status"],
        ),
        (
            "parents",
            ParentProfile.objects.filter(school=school),
            ["id", "relationship", "phone", "address"],
        ),
        (
            "invoices",
            StudentInvoice.objects.filter(school=school),
            ["id", "student_id", "total_amount", "amount_paid", "balance", "status"],
        ),
        (
            "results",
            ResultEntry.objects.filter(school=school),
            ["id", "student_id", "subject_id", "ca_score", "exam_score", "total_score", "grade", "remark", "is_published"],
        ),
    ]

    for name, queryset, fields in datasets:
        file_path = export_dir / f"{name}_{timestamp}.csv"

        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(fields)

            for obj in queryset:
                writer.writerow([getattr(obj, field, "") for field in fields])

        files.append(str(file_path))

    BackupLog.objects.create(
        backup_type=BackupLog.BackupType.SCHOOL_EXPORT,
        status=BackupLog.Status.SUCCESS,
        school=school,
        created_by=user,
        file_path=str(export_dir),
        message=f"School CSV export completed. {len(files)} files generated.",
    )

    return files