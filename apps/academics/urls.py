from django.urls import path
from . import views

urlpatterns = [
    path("", views.academics_dashboard, name="academics_dashboard"),

    path("sessions/", views.session_list, name="academic_session_list"),
    path("sessions/create/", views.session_create, name="academic_session_create"),
    path("sessions/<int:pk>/edit/", views.session_update, name="academic_session_update"),

    path("terms/", views.term_list, name="academic_term_list"),
    path("terms/create/", views.term_create, name="academic_term_create"),
    path("terms/<int:pk>/edit/", views.term_update, name="academic_term_update"),

    path("classes/", views.class_list, name="academic_class_list"),
    path("classes/create/", views.class_create, name="academic_class_create"),
    path("classes/<int:pk>/edit/", views.class_update, name="academic_class_update"),

    path("subjects/", views.subject_list, name="academic_subject_list"),
    path("subjects/create/", views.subject_create, name="academic_subject_create"),
    path("subjects/<int:pk>/edit/", views.subject_update, name="academic_subject_update"),

    path(
        "sessions/rollover/",
        views.session_rollover,
        name="session_rollover",
    ),
]