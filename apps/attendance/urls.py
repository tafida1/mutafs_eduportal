from django.urls import path
from . import views

urlpatterns = [
    path("", views.attendance_dashboard, name="attendance_dashboard"),

    path("students/select/", views.student_attendance_select, name="student_attendance_select"),
    path("students/mark/<int:class_id>/<str:date>/", views.student_attendance_mark, name="student_attendance_mark"),
    path("students/report/", views.student_attendance_report, name="student_attendance_report"),
    path("students/export/csv/", views.student_attendance_export_csv, name="student_attendance_export_csv"),

    path("staff/select/", views.staff_attendance_select, name="staff_attendance_select"),
    path("staff/mark/<str:date>/", views.staff_attendance_mark, name="staff_attendance_mark"),
    path("staff/report/", views.staff_attendance_report, name="staff_attendance_report"),
    path("staff/export/csv/", views.staff_attendance_export_csv, name="staff_attendance_export_csv"),

    path(
        "student/portal/",
        views.student_attendance_portal,
        name="student_attendance_portal"
    ),

    path(
        "parent/portal/",
        views.parent_attendance_portal,
        name="parent_attendance_portal"
    ),
]