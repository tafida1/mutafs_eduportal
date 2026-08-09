from django.urls import path
from . import views

urlpatterns = [
    path("", views.parent_list, name="parent_list"),
    path("create/", views.parent_create, name="parent_create"),
    path("<int:pk>/", views.parent_detail, name="parent_detail"),
    path("<int:pk>/edit/", views.parent_update, name="parent_update"),

    path("portal/dashboard/", views.parent_portal_dashboard, name="parent_portal_dashboard"),
]