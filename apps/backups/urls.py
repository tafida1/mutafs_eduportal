from django.urls import path
from . import views

urlpatterns = [
    path("", views.backup_dashboard, name="backup_dashboard"),
    path("database/run/", views.run_database_backup, name="run_database_backup"),
    path("logs/", views.backup_log_list, name="backup_log_list"),
    path("school-export/", views.school_export_select, name="school_export_select"),
    path("school-export/<int:school_id>/run/", views.run_school_export, name="run_school_export"),
]