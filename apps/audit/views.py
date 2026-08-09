import csv

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render

from apps.accounts.models import User
from apps.core.decorators import role_required
from .models import AuditLog


@login_required
@role_required(User.Role.SUPER_ADMIN, User.Role.SCHOOL_ADMIN)
def audit_dashboard(request):
    logs = AuditLog.objects.select_related("actor", "school")

    if request.user.is_school_admin:
        logs = logs.filter(school=request.user.school)

    context = {
        "total_logs": logs.count(),
        "security_logs": logs.filter(action=AuditLog.Action.SECURITY_BLOCK).count(),
        "create_logs": logs.filter(action=AuditLog.Action.CREATE).count(),
        "update_logs": logs.filter(action=AuditLog.Action.UPDATE).count(),
        "recent_logs": logs[:10],
    }

    return render(request, "audit/dashboard.html", context)


@login_required
@role_required(User.Role.SUPER_ADMIN, User.Role.SCHOOL_ADMIN)
def audit_log_list(request):
    logs = AuditLog.objects.select_related("actor", "school")

    if request.user.is_school_admin:
        logs = logs.filter(school=request.user.school)

    query = request.GET.get("q", "").strip()
    action = request.GET.get("action", "").strip()
    module = request.GET.get("module", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    if query:
        logs = logs.filter(
            Q(actor__username__icontains=query)
            | Q(actor__first_name__icontains=query)
            | Q(actor__last_name__icontains=query)
            | Q(description__icontains=query)
            | Q(ip_address__icontains=query)
            | Q(object_type__icontains=query)
        )

    if action:
        logs = logs.filter(action=action)

    if module:
        logs = logs.filter(module__icontains=module)

    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)

    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)

    return render(request, "audit/log_list.html", {
        "logs": logs,
        "query": query,
        "action": action,
        "module": module,
        "date_from": date_from,
        "date_to": date_to,
        "actions": AuditLog.Action.choices,
    })


@login_required
@role_required(User.Role.SUPER_ADMIN, User.Role.SCHOOL_ADMIN)
def audit_export_csv(request):
    logs = AuditLog.objects.select_related("actor", "school")

    if request.user.is_school_admin:
        logs = logs.filter(school=request.user.school)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="audit_logs.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Date",
        "School",
        "Actor",
        "Action",
        "Module",
        "Object Type",
        "Object ID",
        "IP Address",
        "Description",
    ])

    for log in logs:
        writer.writerow([
            log.created_at,
            log.school.name if log.school else "",
            log.actor.username if log.actor else "System",
            log.get_action_display(),
            log.module,
            log.object_type,
            log.object_id,
            log.ip_address,
            log.description,
        ])

    return response