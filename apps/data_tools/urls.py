from django.urls import path
from . import views

urlpatterns = [
    path("", views.data_tools_dashboard, name="data_tools_dashboard"),

    path(
        "students/template/",
        views.download_student_import_template,
        name="download_student_import_template",
    ),

    path(
        "students/export/",
        views.export_students_csv,
        name="export_students_csv",
    ),

    path(
        "students/import/",
        views.import_students_csv,
        name="import_students_csv",
    ),

    path(
        "students/import/errors/",
        views.student_import_errors,
        name="student_import_errors",
    ),



    path(
        "staff/template/",
        views.download_staff_import_template,
        name="download_staff_import_template",
    ),

    path(
        "staff/export/",
        views.export_staff_csv,
        name="export_staff_csv",
    ),

    path(
        "staff/import/",
        views.import_staff_csv,
        name="import_staff_csv",
    ),

    path(
        "staff/import/errors/",
        views.staff_import_errors,
        name="staff_import_errors",
    ),



    path("parents/template/", views.download_parent_import_template, name="download_parent_import_template"),
    path("parents/export/", views.export_parents_csv, name="export_parents_csv"),
    path("parents/import/", views.import_parents_csv, name="import_parents_csv"),
    path("parents/import/errors/", views.parent_import_errors, name="parent_import_errors"),

    path("cbt/template/", views.download_cbt_question_template, name="download_cbt_question_template"),
    path("cbt/export/", views.export_cbt_questions_csv, name="export_cbt_questions_csv"),
    path("cbt/import/", views.import_cbt_questions_csv, name="import_cbt_questions_csv"),
    path("cbt/import/errors/", views.cbt_import_errors, name="cbt_import_errors"),

    path("results/export/", views.export_results_csv, name="export_results_csv"),
    path("finance/export/", views.export_invoices_csv, name="export_invoices_csv"),
]