from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
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

    def test_duplicate_approval_attempt_does_not_change_approved_membership(self):
        jamiyah = make_jamiyah(self.manager, max_members=2)
        pending = add_membership(
            jamiyah,
            self.member,
            status=Membership.Status.PENDING,
        )
        self.client.force_login(self.manager)

        first_response = self.client.post(
            reverse("manage_join_request", args=[jamiyah.pk, pending.pk]),
            {"action": "approve"},
        )
        second_response = self.client.post(
            reverse("manage_join_request", args=[jamiyah.pk, pending.pk]),
            {"action": "approve"},
        )
        pending.refresh_from_db()

        self.assertRedirects(first_response, reverse("jamiyah_detail", args=[jamiyah.pk]))
        self.assertEqual(second_response.status_code, 404)
        self.assertEqual(pending.status, Membership.Status.APPROVED)
        self.assertEqual(
            Membership.objects.filter(
                jamiyah=jamiyah,
                status=Membership.Status.APPROVED,
            ).count(),
            2,
        )

    def test_rejected_membership_cannot_be_approved_again_by_request_view(self):
        jamiyah = make_jamiyah(self.manager, max_members=3)
        rejected = add_membership(
            jamiyah,
            self.member,
            status=Membership.Status.REJECTED,
        )
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("manage_join_request", args=[jamiyah.pk, rejected.pk]),
            {"action": "approve"},
        )
        rejected.refresh_from_db()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(rejected.status, Membership.Status.REJECTED)

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

    def test_second_payout_schedule_generation_is_rejected(self):
        jamiyah = make_jamiyah(self.manager)
        member_membership = add_membership(jamiyah, self.member)
        manager_membership = Membership.objects.get(jamiyah=jamiyah, user=self.manager)
        self.client.force_login(self.manager)
        member_order = [str(manager_membership.pk), str(member_membership.pk)]

        first_response = self.client.post(
            reverse("generate_payout_schedule", args=[jamiyah.pk]),
            {"member_order": member_order},
        )
        second_response = self.client.post(
            reverse("generate_payout_schedule", args=[jamiyah.pk]),
            {"member_order": member_order},
        )
        jamiyah.refresh_from_db()

        self.assertRedirects(first_response, reverse("jamiyah_detail", args=[jamiyah.pk]))
        self.assertRedirects(second_response, reverse("jamiyah_detail", args=[jamiyah.pk]))
        self.assertEqual(jamiyah.status, Jamiyah.Status.ACTIVE)
        self.assertEqual(PayoutTurn.objects.filter(jamiyah=jamiyah).count(), 2)

    def test_duplicate_payout_position_is_rejected_by_database_constraint(self):
        jamiyah = make_jamiyah(self.manager)
        member_membership = add_membership(jamiyah, self.member)
        manager_membership = Membership.objects.get(jamiyah=jamiyah, user=self.manager)
        PayoutTurn.objects.create(
            jamiyah=jamiyah,
            membership=manager_membership,
            position=1,
            payout_date=jamiyah.start_date,
        )

        with self.assertRaises(IntegrityError):
            PayoutTurn.objects.create(
                jamiyah=jamiyah,
                membership=member_membership,
                position=1,
                payout_date=jamiyah.start_date,
            )

    def test_payout_turn_rejects_cross_jamiyah_membership_on_validation(self):
        other_jamiyah = make_jamiyah(self.other, name="Other Jamiyah")
        jamiyah = make_jamiyah(self.manager)
        foreign_membership = Membership.objects.get(
            jamiyah=other_jamiyah,
            user=self.other,
        )
        turn = PayoutTurn(
            jamiyah=jamiyah,
            membership=foreign_membership,
            position=1,
            payout_date=jamiyah.start_date,
        )

        with self.assertRaises(ValidationError):
            turn.full_clean()

    def test_payout_turn_save_rejects_cross_jamiyah_membership(self):
        other_jamiyah = make_jamiyah(self.other, name="Other Jamiyah")
        jamiyah = make_jamiyah(self.manager)
        foreign_membership = Membership.objects.get(
            jamiyah=other_jamiyah,
            user=self.other,
        )
        turn = PayoutTurn(
            jamiyah=jamiyah,
            membership=foreign_membership,
            position=1,
            payout_date=jamiyah.start_date,
        )

        with self.assertRaises(ValidationError):
            turn.save()
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


class ExploreJamiyahsBusinessRuleTests(TestCase):
    def setUp(self):
        self.manager = make_user("explore_manager", 401)
        self.viewer = make_user("explore_viewer", 402)
        self.public_open = make_jamiyah(
            self.manager,
            name="Public Open Alpha",
            visibility=Jamiyah.Visibility.PUBLIC,
            status=Jamiyah.Status.OPEN,
        )
        self.public_active = make_jamiyah(
            self.manager,
            name="Public Active Alpha",
            visibility=Jamiyah.Visibility.PUBLIC,
            status=Jamiyah.Status.ACTIVE,
        )
        self.public_completed = make_jamiyah(
            self.manager,
            name="Public Completed Alpha",
            visibility=Jamiyah.Visibility.PUBLIC,
            status=Jamiyah.Status.COMPLETED,
        )
        self.public_cancelled = make_jamiyah(
            self.manager,
            name="Public Cancelled Alpha",
            visibility=Jamiyah.Visibility.PUBLIC,
            status=Jamiyah.Status.CANCELLED,
        )
        self.private_open = make_jamiyah(
            self.manager,
            name="Private Open Alpha",
            visibility=Jamiyah.Visibility.PRIVATE,
            status=Jamiyah.Status.OPEN,
        )

    def explore_response(self, params=None):
        self.client.force_login(self.viewer)
        return self.client.get(
            reverse("explore_jamiyahs"),
            params or {},
        )

    def test_public_open_jamiyah_appears_in_explore(self):
        response = self.explore_response()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_open.name)
        self.assertEqual(
            [jamiyah.pk for jamiyah in response.context["jamiyahs"]],
            [self.public_open.pk],
        )

    def test_public_active_completed_and_cancelled_do_not_appear_in_explore(self):
        response = self.explore_response()

        self.assertNotContains(response, self.public_active.name)
        self.assertNotContains(response, self.public_completed.name)
        self.assertNotContains(response, self.public_cancelled.name)

    def test_private_open_jamiyah_does_not_appear_in_explore(self):
        response = self.explore_response()

        self.assertNotContains(response, self.private_open.name)

    def test_search_and_status_parameters_cannot_reveal_other_statuses(self):
        response = self.explore_response(
            {
                "q": "Alpha",
                "status": Jamiyah.Status.ACTIVE,
            }
        )

        self.assertContains(response, self.public_open.name)
        self.assertNotContains(response, self.public_active.name)
        self.assertNotContains(response, self.public_completed.name)
        self.assertNotContains(response, self.public_cancelled.name)
        self.assertNotContains(response, self.private_open.name)

        hidden_search_response = self.explore_response(
            {
                "q": self.public_completed.name,
                "status": Jamiyah.Status.COMPLETED,
            }
        )

        self.assertEqual(hidden_search_response.context["jamiyahs"], [])

    def test_explore_template_no_longer_renders_status_filters(self):
        response = self.explore_response()

        self.assertNotContains(response, "status=active")
        self.assertNotContains(response, "status=completed")
        self.assertNotContains(response, "status=cancelled")

    def test_my_jamiyahs_still_shows_approved_memberships_for_all_statuses(self):
        add_membership(self.public_active, self.viewer)
        add_membership(self.public_completed, self.viewer)
        add_membership(self.public_cancelled, self.viewer)
        add_membership(self.private_open, self.viewer)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("my_jamiyahs"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_active.name)
        self.assertContains(response, self.public_completed.name)
        self.assertContains(response, self.public_cancelled.name)
        self.assertContains(response, self.private_open.name)


class JamiyahEditCancellationTests(TestCase):
    def setUp(self):
        self.manager = make_user("edit_manager", 301)
        self.member = make_user("edit_member", 302)
        self.other = make_user("edit_other", 303)
        self.jamiyah = make_jamiyah(
            self.manager,
            name="Editable Jamiyah",
            max_members=4,
        )

    def edit_payload(self, **overrides):
        data = {
            "name": self.jamiyah.name,
            "description": self.jamiyah.description,
            "contribution_amount": str(self.jamiyah.contribution_amount),
            "max_members": str(self.jamiyah.max_members),
            "frequency": self.jamiyah.frequency,
            "start_date": self.jamiyah.start_date.isoformat(),
            "visibility": self.jamiyah.visibility,
        }
        data.update(overrides)
        return data

    def add_payout_turn(self):
        manager_membership = Membership.objects.get(
            jamiyah=self.jamiyah,
            user=self.manager,
        )
        return PayoutTurn.objects.create(
            jamiyah=self.jamiyah,
            membership=manager_membership,
            position=1,
            payout_date=self.jamiyah.start_date,
        )

    def test_manager_can_edit_open_jamiyah_without_schedule(self):
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("edit_jamiyah", args=[self.jamiyah.pk]),
            self.edit_payload(
                name="Updated Jamiyah",
                description="Updated description.",
                contribution_amount="175.50",
                max_members="5",
                frequency=Jamiyah.Frequency.WEEKLY,
                visibility=Jamiyah.Visibility.PRIVATE,
            ),
        )

        self.jamiyah.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("jamiyah_detail", args=[self.jamiyah.pk]),
        )
        self.assertEqual(self.jamiyah.name, "Updated Jamiyah")
        self.assertEqual(self.jamiyah.description, "Updated description.")
        self.assertEqual(self.jamiyah.contribution_amount, Decimal("175.50"))
        self.assertEqual(self.jamiyah.max_members, 5)
        self.assertEqual(self.jamiyah.frequency, Jamiyah.Frequency.WEEKLY)
        self.assertEqual(self.jamiyah.visibility, Jamiyah.Visibility.PRIVATE)
        self.assertEqual(self.jamiyah.status, Jamiyah.Status.OPEN)
        self.assertEqual(self.jamiyah.creator, self.manager)

    def test_non_manager_cannot_edit_or_cancel_jamiyah(self):
        add_membership(self.jamiyah, self.member)
        self.client.force_login(self.member)

        edit_response = self.client.post(
            reverse("edit_jamiyah", args=[self.jamiyah.pk]),
            self.edit_payload(name="Unauthorized Update"),
        )
        cancel_response = self.client.post(
            reverse("cancel_jamiyah", args=[self.jamiyah.pk])
        )

        self.jamiyah.refresh_from_db()
        self.assertEqual(edit_response.status_code, 404)
        self.assertEqual(cancel_response.status_code, 404)
        self.assertEqual(self.jamiyah.name, "Editable Jamiyah")
        self.assertEqual(self.jamiyah.status, Jamiyah.Status.OPEN)

    def test_anonymous_users_are_redirected_from_edit_and_cancel(self):
        edit_url = reverse("edit_jamiyah", args=[self.jamiyah.pk])
        cancel_url = reverse("cancel_jamiyah", args=[self.jamiyah.pk])

        edit_response = self.client.get(edit_url)
        cancel_response = self.client.get(cancel_url)

        self.assertRedirects(
            edit_response,
            f"{reverse('login')}?next={edit_url}",
        )
        self.assertRedirects(
            cancel_response,
            f"{reverse('login')}?next={cancel_url}",
        )

    def test_active_and_completed_jamiyahs_cannot_be_edited_or_cancelled(self):
        for status in (Jamiyah.Status.ACTIVE, Jamiyah.Status.COMPLETED):
            jamiyah = make_jamiyah(
                self.manager,
                name=f"{status.title()} Jamiyah",
                status=status,
            )
            self.client.force_login(self.manager)

            edit_response = self.client.post(
                reverse("edit_jamiyah", args=[jamiyah.pk]),
                {
                    "name": "Blocked Update",
                    "description": jamiyah.description,
                    "contribution_amount": str(jamiyah.contribution_amount),
                    "max_members": str(jamiyah.max_members),
                    "frequency": jamiyah.frequency,
                    "start_date": jamiyah.start_date.isoformat(),
                    "visibility": jamiyah.visibility,
                },
            )
            cancel_response = self.client.post(
                reverse("cancel_jamiyah", args=[jamiyah.pk])
            )

            jamiyah.refresh_from_db()
            self.assertRedirects(
                edit_response,
                reverse("jamiyah_detail", args=[jamiyah.pk]),
            )
            self.assertRedirects(
                cancel_response,
                reverse("jamiyah_detail", args=[jamiyah.pk]),
            )
            self.assertNotEqual(jamiyah.name, "Blocked Update")
            self.assertEqual(jamiyah.status, status)

    def test_jamiyah_with_payout_turns_cannot_be_edited_or_cancelled(self):
        self.add_payout_turn()
        self.client.force_login(self.manager)

        edit_response = self.client.post(
            reverse("edit_jamiyah", args=[self.jamiyah.pk]),
            self.edit_payload(name="Should Not Save"),
        )
        cancel_response = self.client.post(
            reverse("cancel_jamiyah", args=[self.jamiyah.pk])
        )

        self.jamiyah.refresh_from_db()
        self.assertRedirects(
            edit_response,
            reverse("jamiyah_detail", args=[self.jamiyah.pk]),
        )
        self.assertRedirects(
            cancel_response,
            reverse("jamiyah_detail", args=[self.jamiyah.pk]),
        )
        self.assertEqual(self.jamiyah.name, "Editable Jamiyah")
        self.assertEqual(self.jamiyah.status, Jamiyah.Status.OPEN)

    def test_edit_rejects_invalid_form_values(self):
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("edit_jamiyah", args=[self.jamiyah.pk]),
            self.edit_payload(
                name="   ",
                contribution_amount="0",
            ),
        )

        self.jamiyah.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.context["form"].errors)
        self.assertIn("contribution_amount", response.context["form"].errors)
        self.assertEqual(self.jamiyah.name, "Editable Jamiyah")

    def test_max_members_cannot_drop_below_approved_memberships(self):
        add_membership(self.jamiyah, self.member)
        add_membership(self.jamiyah, self.other)
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("edit_jamiyah", args=[self.jamiyah.pk]),
            self.edit_payload(max_members="2"),
        )

        self.jamiyah.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertIn("max_members", response.context["form"].errors)
        self.assertEqual(self.jamiyah.max_members, 4)

    def test_max_members_cannot_drop_below_pending_requests(self):
        add_membership(self.jamiyah, self.member)
        add_membership(
            self.jamiyah,
            self.other,
            status=Membership.Status.PENDING,
        )
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("edit_jamiyah", args=[self.jamiyah.pk]),
            self.edit_payload(max_members="2"),
        )

        self.jamiyah.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertIn("max_members", response.context["form"].errors)
        self.assertEqual(self.jamiyah.max_members, 4)

    def test_cancellation_requires_confirmation_page_and_post(self):
        self.client.force_login(self.manager)

        get_response = self.client.get(
            reverse("cancel_jamiyah", args=[self.jamiyah.pk])
        )
        self.jamiyah.refresh_from_db()
        self.assertEqual(get_response.status_code, 200)
        self.assertTemplateUsed(get_response, "jamiyahs/cancel.html")
        self.assertEqual(self.jamiyah.status, Jamiyah.Status.OPEN)

        post_response = self.client.post(
            reverse("cancel_jamiyah", args=[self.jamiyah.pk])
        )
        self.jamiyah.refresh_from_db()

        self.assertRedirects(
            post_response,
            reverse("jamiyah_detail", args=[self.jamiyah.pk]),
        )
        self.assertEqual(self.jamiyah.status, Jamiyah.Status.CANCELLED)

    def test_repeated_cancellation_does_not_create_invalid_transition(self):
        self.client.force_login(self.manager)
        self.client.post(reverse("cancel_jamiyah", args=[self.jamiyah.pk]))

        response = self.client.post(
            reverse("cancel_jamiyah", args=[self.jamiyah.pk])
        )
        self.jamiyah.refresh_from_db()

        self.assertRedirects(
            response,
            reverse("jamiyah_detail", args=[self.jamiyah.pk]),
        )
        self.assertEqual(self.jamiyah.status, Jamiyah.Status.CANCELLED)

    def test_cancelled_jamiyah_cannot_be_joined(self):
        self.client.force_login(self.manager)
        self.client.post(reverse("cancel_jamiyah", args=[self.jamiyah.pk]))

        self.client.force_login(self.member)
        response = self.client.post(
            reverse("request_join", args=[self.jamiyah.pk])
        )

        self.assertRedirects(response, reverse("my_jamiyahs"))
        self.assertFalse(
            Membership.objects.filter(
                jamiyah=self.jamiyah,
                user=self.member,
            ).exists()
        )

    def test_cancelled_jamiyah_cannot_generate_schedule(self):
        member_membership = add_membership(self.jamiyah, self.member)
        manager_membership = Membership.objects.get(
            jamiyah=self.jamiyah,
            user=self.manager,
        )
        self.jamiyah.max_members = 2
        self.jamiyah.save(update_fields=["max_members"])
        self.client.force_login(self.manager)
        self.client.post(reverse("cancel_jamiyah", args=[self.jamiyah.pk]))

        response = self.client.post(
            reverse("generate_payout_schedule", args=[self.jamiyah.pk]),
            {
                "member_order": [
                    str(manager_membership.pk),
                    str(member_membership.pk),
                ]
            },
        )

        self.jamiyah.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("jamiyah_detail", args=[self.jamiyah.pk]),
        )
        self.assertEqual(self.jamiyah.status, Jamiyah.Status.CANCELLED)
        self.assertFalse(PayoutTurn.objects.filter(jamiyah=self.jamiyah).exists())

    def test_cancelled_jamiyah_remains_visible_to_manager(self):
        self.client.force_login(self.manager)
        self.client.post(reverse("cancel_jamiyah", args=[self.jamiyah.pk]))

        response = self.client.get(reverse("my_jamiyahs") + "?filter=managed")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.jamiyah.name)

    def test_cancelled_public_jamiyah_is_excluded_from_explore(self):
        self.client.force_login(self.manager)
        self.client.post(reverse("cancel_jamiyah", args=[self.jamiyah.pk]))

        self.client.force_login(self.member)
        response = self.client.get(reverse("explore_jamiyahs"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.jamiyah.name)
