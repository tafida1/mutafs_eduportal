from django.urls import path
from . import views

urlpatterns = [
    path("", views.result_dashboard, name="result_dashboard"),

    path("grades/", views.grade_scale_list, name="grade_scale_list"),
    path("grades/create/", views.grade_scale_create, name="grade_scale_create"),
    path("grades/<int:pk>/edit/", views.grade_scale_update, name="grade_scale_update"),
    path("grades/seed-defaults/", views.seed_default_grade_scales, name="seed_default_grade_scales"),

    path("entry/setup/", views.result_setup, name="result_setup"),
    path(
        "entry/<int:session_id>/<int:term_id>/<int:class_id>/<int:subject_id>/",
        views.result_entry,
        name="result_entry",
    ),

    path(
        "summary/class/<int:session_id>/<int:term_id>/<int:class_id>/",
        views.result_class_summary,
        name="result_class_summary",
    ),

    path(
        "publish/class/<int:session_id>/<int:term_id>/<int:class_id>/",
        views.publish_class_result,
        name="publish_class_result",
    ),

    path(
        "unpublish/class/<int:session_id>/<int:term_id>/<int:class_id>/",
        views.unpublish_class_result,
        name="unpublish_class_result",
    ),

    path(
        "student/<int:student_id>/<int:session_id>/<int:term_id>/",
        views.student_term_result,
        name="student_term_result",
    ),

    path(
        "student/portal/",
        views.student_result_portal,
        name="student_result_portal"
    ),

    path(
        "parent/portal/",
        views.parent_result_portal,
        name="parent_result_portal"
    ),

    path(
        "print/class/<int:session_id>/<int:term_id>/<int:class_id>/",
        views.print_class_results,
        name="print_class_results",
    ),


    path(
        "broadsheet/class/<int:session_id>/<int:term_id>/<int:class_id>/",
        views.class_broadsheet,
        name="class_broadsheet",
    ),


    path(
        "approve/class/<int:session_id>/<int:term_id>/<int:class_id>/",
        views.approve_class_result,
        name="approve_class_result",
    ),

    path(
        "reject/class/<int:session_id>/<int:term_id>/<int:class_id>/",
        views.reject_class_result,
        name="reject_class_result",
    ),


    path(
        "check/",
        views.public_result_checker,
        name="public_result_checker",
    ),


    path(
        "verify/<str:token>/",
        views.verify_result,
        name="verify_result",
    ),
]