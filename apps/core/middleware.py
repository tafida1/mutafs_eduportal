from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class SchoolStatusMiddleware(MiddlewareMixin):
    """
    Blocks users from disabled schools.
    Super Admin is never blocked.
    """

    EXEMPT_URL_NAMES = {
        "login",
        "logout",
        "admin:index",
    }

    def process_request(self, request):
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return None

        if getattr(user, "is_super_admin", False):
            return None

        school = getattr(user, "school", None)

        if school and not school.is_active:
            messages.error(
                request,
                "Your school account has been disabled. Please contact Mutafs Global Technology."
            )
            return redirect("logout")

        return None


class SubscriptionMiddleware(MiddlewareMixin):
    """
    Allows login but warns/restricts expired schools.
    Actual feature restrictions will be enforced per module.
    """

    def process_request(self, request):
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return None

        if getattr(user, "is_super_admin", False):
            return None

        school = getattr(user, "school", None)

        if school and school.is_subscription_expired:
            request.subscription_expired = True
        else:
            request.subscription_expired = False

        return None