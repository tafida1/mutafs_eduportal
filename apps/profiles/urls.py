from django.urls import path
from . import views

urlpatterns = [

    path(
        "me/",
        views.my_profile,
        name="my_profile"
    ),

    path(
        "me/edit/",
        views.edit_profile,
        name="edit_profile"
    ),

    path(
        "me/change-password/",
        views.change_password,
        name="change_password"
    ),

]