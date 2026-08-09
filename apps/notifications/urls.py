from django.urls import path

from . import views

urlpatterns = [
    path("", views.notification_list, name="notification_list"),
    path("<int:pk>/", views.notification_detail, name="notification_detail"),

    path("announcements/", views.announcement_list, name="announcement_list"),
    path("announcements/create/", views.announcement_create, name="announcement_create"),
    path("announcements/<int:pk>/edit/", views.announcement_update, name="announcement_update"),

    path("notice-board/", views.notice_board, name="notice_board"),
]