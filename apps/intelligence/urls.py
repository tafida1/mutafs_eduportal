from django.urls import path
from . import views

urlpatterns = [
    path("my-insight/", views.my_academic_insight, name="my_academic_insight"),
    path("student/<int:student_id>/", views.student_academic_insight, name="student_academic_insight"),
    path("teacher-assistant/", views.teacher_ai_assistant, name="teacher_ai_assistant"),

    path("risk-dashboard/", views.academic_risk_dashboard, name="academic_risk_dashboard"),
    path("my-risk-profile/", views.my_risk_profile, name="my_risk_profile"),
]