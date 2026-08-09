from django.urls import path
from . import views

urlpatterns = [
    path("", views.staff_list, name="staff_list"),
    path("create/", views.staff_create, name="staff_create"),
    path("export/csv/", views.staff_export_csv, name="staff_export_csv"),
    path("<int:pk>/", views.staff_detail, name="staff_detail"),
    path("<int:pk>/edit/", views.staff_update, name="staff_update"),

    path("teacher/workspace/", views.teacher_workspace, name="teacher_workspace"),

    path("teacher/classes/", views.teacher_my_classes, name="teacher_my_classes"),
    path("teacher/classes/<int:class_id>/students/", views.teacher_class_students, name="teacher_class_students"),
    path("teacher/subjects/", views.teacher_my_subjects, name="teacher_my_subjects"),
]