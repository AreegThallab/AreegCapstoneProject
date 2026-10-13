from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import Profile
from .theme import THEME_COOKIE_NAME, THEME_COOKIE_MAX_AGE, THEME_SESSION_KEY


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
class ErrorPageTests(TestCase):
    def test_custom_404_page_renders_without_navbar_for_anonymous_user(self):
        response = self.client.get("/this-page-does-not-exist/")

        self.assertEqual(response.status_code, 404)
        self.assertContains(
            response,
            "يبدو أنك ضيّعت الطريق!",
            status_code=404,
        )
        self.assertContains(
            response,
            "الصفحة اللي تدور عليها غير موجودة، أو يمكن تغيّر رابطها.",
            status_code=404,
        )
        self.assertContains(response, "العودة للرئيسية", status_code=404)
        self.assertContains(response, "العودة للخلف", status_code=404)
        self.assertNotContains(response, 'class="site-header"', status_code=404)
        self.assertNotContains(response, 'id="main-nav"', status_code=404)
        self.assertNotContains(response, 'class="nav-links"', status_code=404)

    def test_anonymous_home_button_and_back_fallback_use_landing_page(self):
        response = self.client.get("/missing-anonymous-page/")
        home_url = reverse("home")

        self.assertEqual(response.status_code, 404)
        self.assertContains(
            response,
            f'href="{home_url}"',
            status_code=404,
        )
        self.assertContains(
            response,
            f'data-fallback-url="{home_url}"',
            status_code=404,
        )

    def test_authenticated_home_button_and_back_fallback_use_dashboard(self):
        user = User.objects.create_user(
            username="notfounduser",
            password="StrongPass123!",
        )
        self.client.force_login(user)

        response = self.client.get("/missing-authenticated-page/")
        dashboard_url = reverse("dashboard")

        self.assertEqual(response.status_code, 404)
        self.assertContains(
            response,
            f'href="{dashboard_url}"',
            status_code=404,
        )
        self.assertContains(
            response,
            f'data-fallback-url="{dashboard_url}"',
            status_code=404,
        )


class ThemePreferenceTests(TestCase):
    def test_default_theme_is_light_without_session_or_cookie(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-theme="light"')
        self.assertContains(response, 'name="theme" value="dark"')

    def test_valid_post_stores_dark_theme_in_session_and_cookie(self):
        response = self.client.post(
            reverse("switch_theme"),
            {"theme": "dark", "next": reverse("home")},
        )

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertEqual(self.client.session[THEME_SESSION_KEY], "dark")
        self.assertEqual(response.cookies[THEME_COOKIE_NAME].value, "dark")
        self.assertEqual(int(response.cookies[THEME_COOKIE_NAME]["max-age"]), THEME_COOKIE_MAX_AGE)
        self.assertEqual(response.cookies[THEME_COOKIE_NAME]["httponly"], True)
        self.assertEqual(response.cookies[THEME_COOKIE_NAME]["samesite"], "Lax")

    def test_valid_post_can_switch_back_to_light(self):
        session = self.client.session
        session[THEME_SESSION_KEY] = "dark"
        session.save()

        response = self.client.post(
            reverse("switch_theme"),
            {"theme": "light", "next": reverse("home")},
        )

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertEqual(self.client.session[THEME_SESSION_KEY], "light")
        self.assertEqual(response.cookies[THEME_COOKIE_NAME].value, "light")

    def test_valid_cookie_restores_theme_into_new_session(self):
        client = Client()
        client.cookies[THEME_COOKIE_NAME] = "dark"

        response = client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-theme="dark"')
        self.assertEqual(client.session[THEME_SESSION_KEY], "dark")

    def test_session_theme_has_priority_over_cookie_theme(self):
        session = self.client.session
        session[THEME_SESSION_KEY] = "light"
        session.save()
        self.client.cookies[THEME_COOKIE_NAME] = "dark"

        response = self.client.get(reverse("home"))

        self.assertContains(response, 'data-theme="light"')

    def test_invalid_session_and_cookie_values_fall_back_to_light(self):
        session = self.client.session
        session[THEME_SESSION_KEY] = "sepia"
        session.save()
        self.client.cookies[THEME_COOKIE_NAME] = "solarized"

        response = self.client.get(reverse("home"))

        self.assertContains(response, 'data-theme="light"')
        self.assertNotIn(THEME_SESSION_KEY, self.client.session)

    def test_invalid_submitted_theme_is_rejected_without_changing_preference(self):
        session = self.client.session
        session[THEME_SESSION_KEY] = "dark"
        session.save()
        self.client.cookies[THEME_COOKIE_NAME] = "dark"

        response = self.client.post(
            reverse("switch_theme"),
            {"theme": "invalid", "next": reverse("home")},
        )

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertEqual(self.client.session[THEME_SESSION_KEY], "dark")
        self.assertNotIn(THEME_COOKIE_NAME, response.cookies)

    def test_theme_switch_requires_post(self):
        response = self.client.get(reverse("switch_theme"), {"theme": "dark"})

        self.assertEqual(response.status_code, 405)
        self.assertNotIn(THEME_SESSION_KEY, self.client.session)

    def test_theme_switch_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)

        response = client.post(
            reverse("switch_theme"),
            {"theme": "dark", "next": reverse("home")},
        )

        self.assertEqual(response.status_code, 403)
        self.assertNotIn(THEME_COOKIE_NAME, response.cookies)

    def test_external_next_url_is_rejected(self):
        response = self.client.post(
            reverse("switch_theme"),
            {"theme": "dark", "next": "https://example.invalid/steal"},
        )

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertEqual(self.client.session[THEME_SESSION_KEY], "dark")

    def test_anonymous_user_can_switch_theme(self):
        response = self.client.post(
            reverse("switch_theme"),
            {"theme": "dark", "next": reverse("login")},
        )

        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)
        self.assertEqual(self.client.session[THEME_SESSION_KEY], "dark")

    def test_authenticated_user_can_switch_theme_and_see_dashboard_in_dark_mode(self):
        user = User.objects.create_user(username="themeuser", password="StrongPass123!")
        Profile.objects.create(
            user=user,
            full_name="Theme User",
            phone_number="+966500000001",
        )
        self.client.force_login(user)

        self.client.post(
            reverse("switch_theme"),
            {"theme": "dark", "next": reverse("dashboard")},
        )
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-theme="dark"')
        self.assertContains(response, 'name="theme" value="light"')

    def test_rendered_templates_do_not_use_theme_javascript_hooks(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{reverse("switch_theme")}"')
        self.assertContains(response, 'method="post"')
        self.assertNotContains(response, "theme.js")
        self.assertNotContains(response, "theme_init")
        self.assertNotContains(response, "data-theme-toggle")
        self.assertNotContains(response, "localStorage")
