from django.utils import timezone

from .models import UserNotification


def notification_context(request):

    if not request.user.is_authenticated:
        return {}

    notifications = UserNotification.objects.select_related(
        "announcement"
    ).filter(
        user=request.user,
        announcement__is_active=True,
        announcement__publish_at__lte=timezone.now(),
        is_read=False,
    )[:5]

    return {
        "global_notifications": notifications,
        "global_unread_notifications_count": notifications.count(),
    }