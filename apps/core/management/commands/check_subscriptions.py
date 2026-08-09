from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.schools.models import School, SchoolSubscription


class Command(BaseCommand):
    help = "Check school subscriptions and mark expired schools."

    def handle(self, *args, **options):
        today = timezone.localdate()

        subscriptions = SchoolSubscription.objects.select_related("school")

        expired_count = 0

        for subscription in subscriptions:
            if subscription.end_date and subscription.end_date < today:
                subscription.status = SchoolSubscription.Status.EXPIRED
                subscription.save(update_fields=["status", "updated_at"])

                school = subscription.school
                school.subscription_status = School.SubscriptionStatus.EXPIRED
                school.is_active = False
                school.save(update_fields=[
                    "subscription_status",
                    "is_active",
                    "updated_at",
                ])

                expired_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Subscription check complete. Expired schools: {expired_count}"
            )
        )