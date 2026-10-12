from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile

from .models import Jamiyah, Membership, PayoutTurn


def make_user(username, phone_suffix):
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="StrongPass123!",
    )
    Profile.objects.create(
        user=user,
        full_name=f"{username.title()} User",
        phone_number=f"+9665{phone_suffix:08d}",
    )
    return user


def make_jamiyah(manager, **overrides):
    defaults = {
        "name": "Test Jamiyah",
        "description": "A test rotating savings group.",
        "creator": manager,
        "contribution_amount": Decimal("100.00"),
        "max_members": 2,
        "frequency": Jamiyah.Frequency.MONTHLY,
        "start_date": timezone.localdate() + timedelta(days=7),
        "visibility": Jamiyah.Visibility.PUBLIC,
        "status": Jamiyah.Status.OPEN,
    }
    defaults.update(overrides)
    jamiyah = Jamiyah.objects.create(**defaults)
    Membership.objects.create(
        jamiyah=jamiyah,
        user=manager,
        role=Membership.Role.MANAGER,
        status=Membership.Status.APPROVED,
    )
    return jamiyah


def add_membership(jamiyah, user, status=Membership.Status.APPROVED):
    return Membership.objects.create(
        jamiyah=jamiyah,
        user=user,
        role=Membership.Role.MEMBER,
        status=status,
    )


class JamiyahWorkflowTests(TestCase):
    def setUp(self):
        self.manager = make_user("manager", 1)
        self.member = make_user("member", 2)
        self.other = make_user("other", 3)

    def test_create_jamiyah_creates_manager_membership(self):
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("create_jamiyah"),
            {
                "name": "Family Fund",
                "description": "Monthly group.",
                "contribution_amount": "250.00",
                "max_members": "3",
                "frequency": Jamiyah.Frequency.MONTHLY,
                "start_date": timezone.localdate() + timedelta(days=5),
                "visibility": Jamiyah.Visibility.PUBLIC,
            },
        )

        jamiyah = Jamiyah.objects.get(name="Family Fund")
        self.assertRedirects(response, reverse("jamiyah_detail", args=[jamiyah.pk]))
        self.assertEqual(jamiyah.creator, self.manager)
        self.assertTrue(
            Membership.objects.filter(
                jamiyah=jamiyah,
                user=self.manager,
                role=Membership.Role.MANAGER,
                status=Membership.Status.APPROVED,
            ).exists()
        )

    def test_create_jamiyah_rejects_past_start_date(self):
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("create_jamiyah"),
            {
                "name": "Past Fund",
                "description": "Invalid date.",
                "contribution_amount": "100.00",
                "max_members": "2",
                "frequency": Jamiyah.Frequency.MONTHLY,
                "start_date": timezone.localdate() - timedelta(days=1),
                "visibility": Jamiyah.Visibility.PUBLIC,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Jamiyah.objects.filter(name="Past Fund").exists())
        self.assertIn("start_date", response.context["form"].errors)

    def test_public_membership_request_and_duplicate_prevention(self):
        jamiyah = make_jamiyah(self.manager)
        self.client.force_login(self.member)

        first_response = self.client.post(reverse("request_join", args=[jamiyah.pk]))
        second_response = self.client.post(reverse("request_join", args=[jamiyah.pk]))

        self.assertRedirects(
            first_response,
            reverse("jamiyah_detail", args=[jamiyah.pk]),
        )
        self.assertRedirects(
            second_response,
            reverse("jamiyah_detail", args=[jamiyah.pk]),
        )
        self.assertEqual(
            Membership.objects.filter(jamiyah=jamiyah, user=self.member).count(),
            1,
        )
        self.assertEqual(
            Membership.objects.get(jamiyah=jamiyah, user=self.member).status,
            Membership.Status.PENDING,
        )

    def test_manager_can_approve_and_reject_join_requests(self):
        jamiyah = make_jamiyah(self.manager, max_members=3)
        approved_request = add_membership(
            jamiyah,
            self.member,
            status=Membership.Status.PENDING,
        )
        rejected_request = add_membership(
            jamiyah,
            self.other,
            status=Membership.Status.PENDING,
        )
        self.client.force_login(self.manager)

        approve_response = self.client.post(
            reverse("manage_join_request", args=[jamiyah.pk, approved_request.pk]),
            {"action": "approve"},
        )
        reject_response = self.client.post(
            reverse("manage_join_request", args=[jamiyah.pk, rejected_request.pk]),
            {"action": "reject"},
        )

        approved_request.refresh_from_db()
        rejected_request.refresh_from_db()
        self.assertRedirects(
            approve_response,
            reverse("jamiyah_detail", args=[jamiyah.pk]),
        )
        self.assertRedirects(
            reject_response,
            reverse("jamiyah_detail", args=[jamiyah.pk]),
        )
        self.assertEqual(approved_request.status, Membership.Status.APPROVED)
        self.assertEqual(rejected_request.status, Membership.Status.REJECTED)

    def test_approval_does_not_exceed_capacity(self):
        jamiyah = make_jamiyah(self.manager, max_members=2)
        pending = add_membership(
            jamiyah,
            self.member,
            status=Membership.Status.PENDING,
        )
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("manage_join_request", args=[jamiyah.pk, pending.pk]),
            {"action": "approve"},
        )
        pending.refresh_from_db()

        self.assertRedirects(response, reverse("jamiyah_detail", args=[jamiyah.pk]))
        self.assertEqual(pending.status, Membership.Status.APPROVED)

        extra = add_membership(
            jamiyah,
            self.other,
            status=Membership.Status.PENDING,
        )
        response = self.client.post(
            reverse("manage_join_request", args=[jamiyah.pk, extra.pk]),
            {"action": "approve"},
        )
        extra.refresh_from_db()

        self.assertRedirects(response, reverse("jamiyah_detail", args=[jamiyah.pk]))
        self.assertEqual(extra.status, Membership.Status.PENDING)
        self.assertEqual(
            Membership.objects.filter(
                jamiyah=jamiyah,
                status=Membership.Status.APPROVED,
            ).count(),
            jamiyah.max_members,
        )

    def test_generate_payout_schedule_activates_jamiyah(self):
        jamiyah = make_jamiyah(self.manager)
        member_membership = add_membership(jamiyah, self.member)
        manager_membership = Membership.objects.get(jamiyah=jamiyah, user=self.manager)
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("generate_payout_schedule", args=[jamiyah.pk]),
            {
                "member_order": [
                    str(manager_membership.pk),
                    str(member_membership.pk),
                ]
            },
        )

        jamiyah.refresh_from_db()
        turns = list(PayoutTurn.objects.filter(jamiyah=jamiyah).order_by("position"))
        self.assertRedirects(response, reverse("jamiyah_detail", args=[jamiyah.pk]))
        self.assertEqual(jamiyah.status, Jamiyah.Status.ACTIVE)
        self.assertEqual(len(turns), 2)
        self.assertEqual(turns[0].membership, manager_membership)
        self.assertEqual(turns[1].membership, member_membership)
        self.assertEqual(turns[0].payout_date, jamiyah.start_date)

    def test_generate_schedule_rejects_duplicate_member_order(self):
        jamiyah = make_jamiyah(self.manager)
        add_membership(jamiyah, self.member)
        manager_membership = Membership.objects.get(jamiyah=jamiyah, user=self.manager)
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("generate_payout_schedule", args=[jamiyah.pk]),
            {
                "member_order": [
                    str(manager_membership.pk),
                    str(manager_membership.pk),
                ]
            },
        )

        jamiyah.refresh_from_db()
        self.assertRedirects(response, reverse("jamiyah_detail", args=[jamiyah.pk]))
        self.assertEqual(jamiyah.status, Jamiyah.Status.OPEN)
        self.assertFalse(PayoutTurn.objects.filter(jamiyah=jamiyah).exists())

    def test_private_jamiyah_detail_is_restricted_to_approved_members(self):
        jamiyah = make_jamiyah(
            self.manager,
            visibility=Jamiyah.Visibility.PRIVATE,
        )
        self.client.force_login(self.other)

        response = self.client.get(reverse("jamiyah_detail", args=[jamiyah.pk]))

        self.assertEqual(response.status_code, 404)

    def test_non_manager_cannot_manage_requests_or_generate_schedule(self):
        jamiyah = make_jamiyah(self.manager, max_members=3)
        member_membership = add_membership(jamiyah, self.member)
        pending = add_membership(
            jamiyah,
            self.other,
            status=Membership.Status.PENDING,
        )
        self.client.force_login(self.member)

        manage_response = self.client.post(
            reverse("manage_join_request", args=[jamiyah.pk, pending.pk]),
            {"action": "approve"},
        )
        schedule_response = self.client.post(
            reverse("generate_payout_schedule", args=[jamiyah.pk]),
            {"member_order": [str(member_membership.pk)]},
        )

        self.assertEqual(manage_response.status_code, 404)
        self.assertEqual(schedule_response.status_code, 404)
