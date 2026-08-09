from django.shortcuts import render


class TenantMaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            school = getattr(user, "school", None)

            if school and school.maintenance_mode:
                if not user.is_super_admin and not user.is_school_admin:
                    return render(
                        request,
                        "schools/maintenance.html",
                        {"school": school},
                        status=503,
                    )

        return self.get_response(request)