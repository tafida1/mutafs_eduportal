from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from apps.audit.services import log_audit

from .forms import (
    ProfileUpdateForm,
    StyledPasswordChangeForm,
)


@login_required
def my_profile(request):

    return render(request, "profiles/my_profile.html", {
        "user_obj": request.user,
    })


@login_required
def edit_profile(request):

    if request.method == "POST":

        form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )

        if form.is_valid():

            user = form.save()

            log_audit(
                request=request,
                school=user.school,
                action="UPDATE",
                module="profiles",
                object_type="UserProfile",
                object_id=user.id,
                description=f"{user.email} updated profile",
            )

            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect("my_profile")

    else:

        form = ProfileUpdateForm(
            instance=request.user
        )

    return render(request, "profiles/edit_profile.html", {
        "form": form,
    })


@login_required
def change_password(request):

    if request.method == "POST":

        form = StyledPasswordChangeForm(
            user=request.user,
            data=request.POST
        )

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(
                request,
                user
            )

            log_audit(
                request=request,
                school=user.school,
                action="UPDATE",
                module="security",
                object_type="Password",
                object_id=user.id,
                description=f"{user.email} changed password",
            )

            messages.success(
                request,
                "Password changed successfully."
            )

            return redirect("my_profile")

    else:

        form = StyledPasswordChangeForm(
            user=request.user
        )

    return render(request, "profiles/change_password.html", {
        "form": form,
    })