from django.urls import path
from . import views

urlpatterns = [
    path("", views.cbt_dashboard, name="cbt_dashboard"),

    path("questions/", views.question_list, name="cbt_question_list"),
    path("questions/create/", views.question_create, name="cbt_question_create"),
    path("questions/<int:pk>/edit/", views.question_update, name="cbt_question_update"),

    path("exams/", views.exam_list, name="cbt_exam_list"),
    path("exams/create/", views.exam_create, name="cbt_exam_create"),
    path("exams/<int:pk>/", views.exam_detail, name="cbt_exam_detail"),
    path("exams/<int:pk>/edit/", views.exam_update, name="cbt_exam_update"),
    path("exams/<int:pk>/toggle/", views.exam_toggle_status, name="cbt_exam_toggle_status"),

    path("student/", views.student_cbt_dashboard, name="student_cbt_dashboard"),
    path("student/start/<int:exam_id>/", views.start_exam, name="start_exam"),
    path("student/take/<int:attempt_id>/", views.take_exam, name="take_exam"),
    path("attempt/<int:attempt_id>/result/", views.attempt_result, name="cbt_attempt_result"),

    path("reports/attempts/", views.cbt_attempts_report, name="cbt_attempts_report"),
]