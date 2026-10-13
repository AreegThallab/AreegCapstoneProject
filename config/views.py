
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .theme import (
    THEME_SESSION_KEY,
    is_valid_theme,
    safe_next_url,
    set_theme_cookie,
)


def home(request):
    return render(request, "home.html")


@login_required
def dashboard(request):
    return render(request, "dashboard/home.html")


@require_POST
def switch_theme(request):
    requested_theme = request.POST.get("theme")
    response = redirect(safe_next_url(request))

    if not is_valid_theme(requested_theme):
        return response

    request.session[THEME_SESSION_KEY] = requested_theme
    return set_theme_cookie(response, requested_theme)
