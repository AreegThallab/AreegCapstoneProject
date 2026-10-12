from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.reports_dashboard,
        name="reports_dashboard"
    ),
    path(
        "jamiyah/<int:pk>/",
        views.jamiyah_report,
        name="jamiyah_report"
    ),
]
