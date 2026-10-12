from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse


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
