def global_context(request):
    user = getattr(request, "user", None)

    current_school = None
    subscription_expired = False

    if user and user.is_authenticated:
        current_school = getattr(user, "school", None)
        subscription_expired = getattr(request, "subscription_expired", False)

    return {
        "APP_NAME": "Mutafs EduPortal SaaS",
        "COMPANY_NAME": "Mutafs Global Technology",
        "current_school": current_school,
        "subscription_expired": subscription_expired,
    }