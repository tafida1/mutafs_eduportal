from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, include
from django.contrib.auth import views as auth_views
from apps.core import views as core_views


urlpatterns = [
    path("admin/", admin.site.urls),

    path("ckeditor/", include("ckeditor_uploader.urls")),

    path(
        "",
        LoginView.as_view(
            template_name="accounts/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),

    path("logout/", LogoutView.as_view(), name="logout"),
    path("dashboard/", core_views.dashboard_router, name="dashboard_router"),

    path("dashboard/super-admin/", core_views.super_admin_dashboard, name="super_admin_dashboard"),
    path("dashboard/school-admin/", core_views.school_admin_dashboard, name="school_admin_dashboard"),
    path("dashboard/teacher/", core_views.teacher_dashboard, name="teacher_dashboard"),
    path("dashboard/student/", core_views.student_dashboard, name="student_dashboard"),
    path("dashboard/parent/", core_views.parent_dashboard, name="parent_dashboard"),

    path("schools/", include("apps.schools.urls")),
    path("academics/", include("apps.academics.urls")),
    path("students/", include("apps.students.urls")),
    path("parents/", include("apps.parents.urls")),
    path("staffs/", include("apps.staffs.urls")),
    path("attendance/", include("apps.attendance.urls")),
    path("results/", include("apps.results.urls")),
    path("cbt/", include("apps.cbt.urls")),
    path("lessons/", include("apps.lessons.urls")),
    path("timetable/", include("apps.timetable.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("finance/", include("apps.finance.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("audit/", include("apps.audit.urls")),
    path(
        "account/password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            success_url="/account/password-change/done/",
        ),
        name="password_change",
    ),

    path(
        "account/password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html",
        ),
        name="password_change_done",
    ),
    path("", include("apps.public_portal.urls")),

    path("profile/", include("apps.profiles.urls")),

    path("backups/", include("apps.backups.urls")),

    path("messages/", include("apps.messaging.urls")),
    path("intelligence/", include("apps.intelligence.urls")),
    path("data-tools/", include("apps.data_tools.urls")),

    path("accounts/", include("apps.accounts.urls")),

    path("about/", core_views.public_about, name="public_about"),
    path("contact/", core_views.public_contact, name="public_contact"),
    path("mission-vision/", core_views.public_mission_vision, name="public_mission_vision"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




handler404 = "apps.core.views.custom_404"
handler500 = "apps.core.views.custom_500"
handler403 = "apps.core.views.custom_403"