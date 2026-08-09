def tenant_context(request):
    school = None

    if request.user.is_authenticated:
        school = getattr(request.user, "school", None)

    return {
        "tenant_school": school,
    }