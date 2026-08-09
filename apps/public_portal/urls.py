from django.urls import path
from . import views

urlpatterns = [
    path(
        "results/<slug:portal_subpath>/",
        views.result_portal_home,
        name="public_result_portal",
    ),
    path(
        "results/<slug:portal_subpath>/check/",
        views.result_checker_submit,
        name="public_result_checker_submit",
    ),
    path(
        "results/<slug:portal_subpath>/student/<str:token>/<int:session_id>/<int:term_id>/",
        views.public_student_result,
        name="public_student_result",
    ),
    path(
        "verify/result/<str:token>/",
        views.verify_result_qr,
        name="verify_result_qr",
    ),
]