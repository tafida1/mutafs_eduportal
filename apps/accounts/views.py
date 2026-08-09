from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.shortcuts import redirect, render


@login_required
def force_password_change(request):
    if not getattr(request.user, "must_change_password", False):
        return redirect("dashboard_router")

    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            user.must_change_password = False
            user.save(update_fields=["must_change_password"])
            update_session_auth_hash(request, user)

            messages.success(request, "Password changed successfully.")
            return redirect("dashboard_router")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "accounts/force_password_change.html", {
        "form": form,
    })