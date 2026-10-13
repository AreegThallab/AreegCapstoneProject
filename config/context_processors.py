from .theme import opposite_theme, resolve_theme


def active_theme(request):
    theme = resolve_theme(request)
    return {
        "active_theme": theme,
        "next_theme": opposite_theme(theme),
    }
