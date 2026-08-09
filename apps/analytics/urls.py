from django.urls import path
from . import views

urlpatterns = [
    path("", views.analytics_dashboard, name="analytics_dashboard"),
    path("global/", views.global_analytics_dashboard, name="global_analytics_dashboard"),
]