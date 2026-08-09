from django.urls import path
from . import views

urlpatterns = [
    path("", views.student_list, name="student_list"),
    path("create/", views.student_create, name="student_create"),
    path("export/csv/", views.student_export_csv, name="student_export_csv"),
    path("cards/school/", views.school_passkey_cards, name="school_passkey_cards"),
    path("cards/class/<int:class_id>/", views.class_passkey_cards, name="class_passkey_cards"),
    path("<int:pk>/", views.student_detail, name="student_detail"),
    path("<int:pk>/edit/", views.student_update, name="student_update"),
    path("<int:pk>/passkey-card/", views.student_passkey_card, name="student_passkey_card"),
    path(
        "movement/",
        views.student_class_movement,
        name="student_class_movement",
    ),

    path(
        "promotion-wizard/",
        views.smart_promotion_wizard,
        name="smart_promotion_wizard",
    ),
]