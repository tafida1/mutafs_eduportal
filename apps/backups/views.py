from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import User
from apps.core.decorators import role_required
from apps.schools.models import School
from .models import BackupLog
from .services import export_school_data_csv


@login_required
@role_required(User.Role.SUPER_ADMIN)
def backup_dashboard(request):
    logs = BackupLog.objects.select_related("school", "created_by")[:20]

    context = {
        "total_backups": BackupLog.objects.count(),
        "success_backups": BackupLog.objects.filter(status=BackupLog.Status.SUCCESS).count(),
        "failed_backups": BackupLog.objects.filter(status=BackupLog.Status.FAILED).count(),
        "database_backups": BackupLog.objects.filter(backup_type=BackupLog.BackupType.DATABASE).count(),
        "recent_logs": logs,
    }

    return render(request, "backups/dashboard.html", context)


@login_required
@role_required(User.Role.SUPER_ADMIN)
def run_database_backup(request):
    try:
        call_command("backup_database")
        messages.success(request, "Database backup completed successfully.")
    except Exception as e:
        messages.error(request, f"Database backup failed: {e}")

    return redirect("backup_dashboard")


@login_required
@role_required(User.Role.SUPER_ADMIN)
def backup_log_list(request):
    logs = BackupLog.objects.select_related("school", "created_by")

    return render(request, "backups/log_list.html", {
        "logs": logs,
    })


@login_required
@role_required(User.Role.SUPER_ADMIN)
def school_export_select(request):
    schools = School.objects.all().order_by("name")

    return render(request, "backups/school_export_select.html", {
        "schools": schools,
    })


@login_required
@role_required(User.Role.SUPER_ADMIN)
def run_school_export(request, school_id):
    school = get_object_or_404(School, pk=school_id)

    try:
        export_school_data_csv(school=school, user=request.user)
        messages.success(request, f"{school.name} data exported successfully.")
    except Exception as e:
        BackupLog.objects.create(
            backup_type=BackupLog.BackupType.SCHOOL_EXPORT,
            status=BackupLog.Status.FAILED,
            school=school,
            created_by=request.user,
            message=str(e),
        )
        messages.error(request, f"School export failed: {e}")

    return redirect("backup_dashboard")