from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.audit.services import log_audit
from apps.core.decorators import role_required
from django.db import models
from .forms import AnnouncementForm
from .models import Announcement, UserNotification
from .services import distribute_announcement


def current_school(request):
    return request.user.school


@login_required
def notification_list(request):

    notifications = request.user.notifications.select_related(
        "announcement"
    ).filter(
        announcement__is_active=True,
        announcement__publish_at__lte=timezone.now(),
    )

    return render(request, "notifications/notification_list.html", {
        "notifications": notifications,
    })


@login_required
def notification_detail(request, pk):

    notification = get_object_or_404(
        UserNotification.objects.select_related("announcement"),
        pk=pk,
        user=request.user,
    )

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(
            update_fields=["is_read", "read_at"]
        )

    return render(request, "notifications/notification_detail.html", {
        "notification": notification,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def announcement_list(request):

    school = current_school(request)

    announcements = Announcement.objects.filter(
        school=school
    )

    return render(request, "notifications/announcement_list.html", {
        "announcements": announcements,
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def announcement_create(request):

    school = current_school(request)

    if request.method == "POST":

        form = AnnouncementForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            announcement = form.save(commit=False)
            announcement.school = school
            announcement.created_by = request.user
            announcement.save()

            distribute_announcement(announcement)

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.CREATE,
                module="notifications",
                object_type="Announcement",
                object_id=announcement.id,
                description=f"Created announcement: {announcement.title}",
            )

            messages.success(
                request,
                "Announcement created successfully."
            )

            return redirect("announcement_list")

    else:
        form = AnnouncementForm()

    return render(request, "notifications/form.html", {
        "form": form,
        "title": "Create Announcement",
    })


@login_required
@role_required(User.Role.SCHOOL_ADMIN)
def announcement_update(request, pk):

    school = current_school(request)

    announcement = get_object_or_404(
        Announcement,
        pk=pk,
        school=school,
    )

    if request.method == "POST":

        form = AnnouncementForm(
            request.POST,
            request.FILES,
            instance=announcement,
        )

        if form.is_valid():

            announcement = form.save()

            log_audit(
                request=request,
                school=school,
                action=AuditLog.Action.UPDATE,
                module="notifications",
                object_type="Announcement",
                object_id=announcement.id,
                description=f"Updated announcement: {announcement.title}",
            )

            messages.success(
                request,
                "Announcement updated successfully."
            )

            return redirect("announcement_list")

    else:
        form = AnnouncementForm(instance=announcement)

    return render(request, "notifications/form.html", {
        "form": form,
        "title": "Edit Announcement",
    })



@login_required
def notice_board(request):
    from django.utils import timezone

    school = request.user.school

    announcements = Announcement.objects.filter(
        school=school,
        is_active=True,
    ).filter(
        models.Q(expires_at__isnull=True) |
        models.Q(expires_at__gte=timezone.now())
    ).order_by(
        "-is_pinned",
        "-created_at",
    )

    return render(request, "notifications/notice_board.html", {
        "announcements": announcements,
    })