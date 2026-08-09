from django.urls import path
from . import views

urlpatterns = [
    path("", views.timetable_dashboard, name="timetable_dashboard"),

    path("slots/", views.time_slot_list, name="time_slot_list"),
    path("slots/create/", views.time_slot_create, name="time_slot_create"),
    path("slots/<int:pk>/edit/", views.time_slot_update, name="time_slot_update"),

    path("entries/", views.timetable_entry_list, name="timetable_entry_list"),
    path("entries/create/", views.timetable_entry_create, name="timetable_entry_create"),
    path("entries/<int:pk>/edit/", views.timetable_entry_update, name="timetable_entry_update"),

    path("class/<int:class_id>/", views.timetable_class_view, name="timetable_class_view"),
    path("my-class/", views.timetable_class_view, name="student_class_timetable"),

    path("teacher/<int:staff_id>/", views.teacher_timetable_view, name="teacher_timetable_view"),
    path("my-teacher-timetable/", views.teacher_timetable_view, name="my_teacher_timetable"),
]