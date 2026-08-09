from django.conf import settings
from django.core.mail import send_mail


def send_system_email(*, subject, message, recipient_list):
    if not recipient_list:
        return False

    return send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=recipient_list,
        fail_silently=True,
    )