from .models import MessageReadStatus


def unread_messages_count(request):
    if not request.user.is_authenticated:
        return {
            "global_unread_messages_count": 0,
        }

    count = MessageReadStatus.objects.filter(
        user=request.user,
        is_read=False,
    ).count()

    return {
        "global_unread_messages_count": count,
    }