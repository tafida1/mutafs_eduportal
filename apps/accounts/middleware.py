from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            must_change = getattr(user, "must_change_password", False)

            allowed_paths = [
                reverse("force_password_change"),
                reverse("logout"),
            ]

            if must_change and request.path not in allowed_paths:
                return redirect("force_password_change")

        return self.get_response(request)