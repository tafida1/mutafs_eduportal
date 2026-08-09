from django.conf import settings
from django.core.management.base import BaseCommand

from apps.core.qr_utils import generate_qr_image
from apps.students.models import StudentProfile


class Command(BaseCommand):
    help = "Generate missing result QR codes for students"

    def handle(self, *args, **options):
        students = StudentProfile.objects.filter(result_qr="")

        count = 0

        for student in students:
            if not student.result_token:
                student.save()

            verify_url = f"{settings.SITE_URL}/verify/result/{student.result_token}/"

            qr_file = generate_qr_image(
                verify_url,
                filename=f"student_{student.id}_result_qr.png",
            )

            student.result_qr.save(qr_file.name, qr_file, save=True)
            count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Generated QR codes for {count} students.")
        )