from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
from django.urls import path, include


urlpatterns = [
    # Registration
    path(
        "register/",
        views.register_view,
        name="register"
    ),

    # Login
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html"
        ),
        name="login"
    ),

    # Logout
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout"
    ),
    path("profile/", views.profile_view, name="profile"),
    path("jamiyahs/", include("jamiyahs.urls")),
    path("reports/", include("reports.urls")),
]
