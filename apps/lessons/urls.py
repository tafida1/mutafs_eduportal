from django.urls import path
from . import views

urlpatterns = [
    path("", views.lesson_dashboard, name="lesson_dashboard"),
    path("resources/", views.lesson_list, name="lesson_list"),
    path("resources/create/", views.lesson_create, name="lesson_create"),
    path("resources/<int:pk>/", views.lesson_detail, name="lesson_detail"),
    path("resources/<int:pk>/edit/", views.lesson_update, name="lesson_update"),
    path("resources/<int:pk>/toggle-publish/", views.lesson_toggle_publish, name="lesson_toggle_publish"),
]