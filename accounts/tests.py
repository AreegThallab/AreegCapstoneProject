from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Profile


class RegistrationAuthenticationTests(TestCase):
    def test_user_can_register_and_authenticate(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "full_name": "New User",
                "email": "new@example.com",
                "phone_number": "+966500000001",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(
            Profile.objects.filter(
                user=user,
                full_name="New User",
                phone_number="+966500000001",
            ).exists()
        )
        self.assertTrue(
            self.client.login(username="newuser", password="StrongPass123!")
        )

    def test_registration_rejects_duplicate_email_and_phone(self):
        existing = User.objects.create_user(
            username="existing",
            email="used@example.com",
            password="StrongPass123!",
        )
        Profile.objects.create(
            user=existing,
            full_name="Existing User",
            phone_number="+966500000002",
        )

        response = self.client.post(
            reverse("register"),
            {
                "username": "candidate",
                "full_name": "Candidate User",
                "email": "USED@example.com",
                "phone_number": "+966500000002",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="candidate").exists())
        self.assertIn("email", response.context["form"].errors)
        self.assertIn("phone_number", response.context["form"].errors)

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])
