from django.urls import path
from . import views

urlpatterns = [
    path("", views.audit_dashboard, name="audit_dashboard"),
    path("logs/", views.audit_log_list, name="audit_log_list"),
    path("logs/export/csv/", views.audit_export_csv, name="audit_export_csv"),
]