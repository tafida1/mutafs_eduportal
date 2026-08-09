from django.utils import timezone

from apps.accounts.models import User
from .models import UserNotification


def get_target_users(school, audience):

    queryset = User.objects.filter(
        school=school,
        is_active=True,
    )

    if audience == "ALL":
        return queryset

    if audience == "TEACHERS":
        return queryset.filter(role=User.Role.TEACHER)

    if audience == "STUDENTS":
        return queryset.filter(role=User.Role.STUDENT)

    if audience == "PARENTS":
        return queryset.filter(role=User.Role.PARENT)

    if audience == "SCHOOL_ADMINS":
        return queryset.filter(role=User.Role.SCHOOL_ADMIN)

    return queryset.none()


def distribute_announcement(announcement):

    users = get_target_users(
        school=announcement.school,
        audience=announcement.audience,
    )

    notifications = []

    for user in users:
        notifications.append(
            UserNotification(
                user=user,
                announcement=announcement,
            )
        )

    UserNotification.objects.bulk_create(
        notifications,
        ignore_conflicts=True,
    )


def unread_notifications(user):
    return user.notifications.filter(is_read=False)