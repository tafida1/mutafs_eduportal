from .models import AuditLog


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def log_audit(
    *,
    request=None,
    actor=None,
    school=None,
    action,
    module="",
    object_type="",
    object_id="",
    description="",
):
    if request:
        actor = actor or getattr(request, "user", None)

        if actor and actor.is_anonymous:
            actor = None

        school = school or getattr(actor, "school", None)

        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
    else:
        ip_address = None
        user_agent = ""

    return AuditLog.objects.create(
        actor=actor,
        school=school,
        action=action,
        module=module,
        object_type=object_type,
        object_id=str(object_id) if object_id else "",
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )