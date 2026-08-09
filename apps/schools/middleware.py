from django.shortcuts import redirect
from django.utils import timezone

from apps.schools.models import School




class SubscriptionMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        user = getattr(request, "user", None)

        if user and user.is_authenticated:

            school = getattr(user, "school", None)

            if school:
                if (
                    school.subscription_end_date
                    and school.subscription_end_date < timezone.now().date()
                ):
                    school.subscription_status = school.SubscriptionStatus.EXPIRED
                    school.is_active = False
                    school.save(
                        update_fields=[
                            "subscription_status",
                            "is_active",
                            "updated_at",
                        ]
                    )

        return self.get_response(request)