from django.conf import settings
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


THEME_COOKIE_NAME = "dawrah_theme"
THEME_COOKIE_MAX_AGE = 60 * 60 * 24 * 365
THEME_SESSION_KEY = "dawrah_theme"
DEFAULT_THEME = "light"
VALID_THEMES = {"light", "dark"}


def is_valid_theme(theme):
    return theme in VALID_THEMES


def opposite_theme(theme):
    return "light" if theme == "dark" else "dark"


def resolve_theme(request):
    session_theme = request.session.get(THEME_SESSION_KEY)
    if is_valid_theme(session_theme):
        return session_theme

    if session_theme is not None:
        request.session.pop(THEME_SESSION_KEY, None)

    cookie_theme = request.COOKIES.get(THEME_COOKIE_NAME)
    if is_valid_theme(cookie_theme):
        request.session[THEME_SESSION_KEY] = cookie_theme
        return cookie_theme

    return DEFAULT_THEME


def safe_next_url(request):
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("home")
    if url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url

    return reverse("home")


def set_theme_cookie(response, theme):
    response.set_cookie(
        THEME_COOKIE_NAME,
        theme,
        max_age=THEME_COOKIE_MAX_AGE,
        path="/",
        secure=not settings.DEBUG,
        httponly=True,
        samesite="Lax",
    )
    return response
