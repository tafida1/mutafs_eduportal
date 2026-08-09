import shutil
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.backups.models import BackupLog


class Command(BaseCommand):
    help = "Create a local database backup"

    def handle(self, *args, **options):
        backup_dir = Path(settings.BASE_DIR) / "backups" / "database"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")

        db_engine = settings.DATABASES["default"]["ENGINE"]

        try:
            if "sqlite" in db_engine:
                db_path = Path(settings.DATABASES["default"]["NAME"])
                backup_file = backup_dir / f"db_backup_{timestamp}.sqlite3"

                shutil.copy2(db_path, backup_file)

                BackupLog.objects.create(
                    backup_type=BackupLog.BackupType.DATABASE,
                    status=BackupLog.Status.SUCCESS,
                    file_path=str(backup_file),
                    message="SQLite database backup completed successfully.",
                )

                self.stdout.write(
                    self.style.SUCCESS(f"Database backup created: {backup_file}")
                )

            else:
                BackupLog.objects.create(
                    backup_type=BackupLog.BackupType.DATABASE,
                    status=BackupLog.Status.FAILED,
                    message="Automatic PostgreSQL backup requires pg_dump setup.",
                )

                self.stdout.write(
                    self.style.WARNING(
                        "PostgreSQL detected. Use pg_dump in production deployment."
                    )
                )

        except Exception as e:
            BackupLog.objects.create(
                backup_type=BackupLog.BackupType.DATABASE,
                status=BackupLog.Status.FAILED,
                message=str(e),
            )

            raise