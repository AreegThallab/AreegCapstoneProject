from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from jamiyahs.models import Jamiyah, Membership, PayoutTurn
from jamiyahs.tests import add_membership, make_jamiyah, make_user

from .models import Payment


def activate_jamiyah(jamiyah, ordered_memberships):
    turns = []
    for position, membership in enumerate(ordered_memberships, start=1):
        turns.append(
            PayoutTurn.objects.create(
                jamiyah=jamiyah,
                membership=membership,
                position=position,
                payout_date=jamiyah.start_date,
            )
        )
    jamiyah.status = Jamiyah.Status.ACTIVE
    jamiyah.save(update_fields=["status"])
    return turns


class PaymentWorkflowTests(TestCase):
    def setUp(self):
        self.manager = make_user("manager", 101)
        self.member = make_user("member", 102)
        self.other = make_user("other", 103)
        self.jamiyah = make_jamiyah(self.manager)
        self.manager_membership = Membership.objects.get(
            jamiyah=self.jamiyah,
            user=self.manager,
        )
        self.member_membership = add_membership(self.jamiyah, self.member)
        self.turns = activate_jamiyah(
            self.jamiyah,
            [self.manager_membership, self.member_membership],
        )

    def test_member_reports_payment_and_duplicate_pending_is_prevented(self):
        self.client.force_login(self.member)

        first_response = self.client.post(
            reverse("report_payment", args=[self.jamiyah.pk, self.turns[0].pk])
        )
        second_response = self.client.post(
            reverse("report_payment", args=[self.jamiyah.pk, self.turns[0].pk])
        )

        self.assertRedirects(
            first_response,
            reverse("payment_dashboard", args=[self.jamiyah.pk]),
        )
        self.assertRedirects(
            second_response,
            reverse("payment_dashboard", args=[self.jamiyah.pk]),
        )
        self.assertEqual(
            Payment.objects.filter(
                jamiyah=self.jamiyah,
                membership=self.member_membership,
                payout_turn=self.turns[0],
            ).count(),
            1,
        )
        self.assertEqual(
            Payment.objects.get(
                jamiyah=self.jamiyah,
                membership=self.member_membership,
                payout_turn=self.turns[0],
            ).status,
            Payment.Status.PENDING,
        )

    def test_manager_verifies_payment_and_verified_duplicate_is_prevented(self):
        payment = Payment.objects.create(
            jamiyah=self.jamiyah,
            membership=self.member_membership,
            payout_turn=self.turns[0],
            status=Payment.Status.PENDING,
        )
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("review_payment", args=[self.jamiyah.pk, payment.pk]),
            {"action": "verify"},
        )
        payment.refresh_from_db()
        before = Payment.objects.count()

        self.client.force_login(self.member)
        duplicate_response = self.client.post(
            reverse("report_payment", args=[self.jamiyah.pk, self.turns[0].pk])
        )

        self.assertRedirects(
            response,
            reverse("payment_dashboard", args=[self.jamiyah.pk]),
        )
        self.assertEqual(payment.status, Payment.Status.VERIFIED)
        self.assertEqual(payment.reviewed_by, self.manager)
        self.assertIsNotNone(payment.reviewed_at)
        self.assertRedirects(
            duplicate_response,
            reverse("payment_dashboard", args=[self.jamiyah.pk]),
        )
        self.assertEqual(Payment.objects.count(), before)

    def test_manager_rejects_payment_and_member_can_resubmit(self):
        payment = Payment.objects.create(
            jamiyah=self.jamiyah,
            membership=self.member_membership,
            payout_turn=self.turns[0],
            status=Payment.Status.PENDING,
        )
        self.client.force_login(self.manager)

        reject_response = self.client.post(
            reverse("review_payment", args=[self.jamiyah.pk, payment.pk]),
            {"action": "reject"},
        )
        payment.refresh_from_db()

        self.client.force_login(self.member)
        resubmit_response = self.client.post(
            reverse("report_payment", args=[self.jamiyah.pk, self.turns[0].pk])
        )
        payment.refresh_from_db()

        self.assertRedirects(
            reject_response,
            reverse("payment_dashboard", args=[self.jamiyah.pk]),
        )
        self.assertRedirects(
            resubmit_response,
            reverse("payment_dashboard", args=[self.jamiyah.pk]),
        )
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertIsNone(payment.reviewed_by)
        self.assertIsNone(payment.reviewed_at)
        self.assertEqual(
            Payment.objects.filter(
                jamiyah=self.jamiyah,
                membership=self.member_membership,
                payout_turn=self.turns[0],
            ).count(),
            1,
        )

    def test_non_manager_cannot_review_payment(self):
        payment = Payment.objects.create(
            jamiyah=self.jamiyah,
            membership=self.member_membership,
            payout_turn=self.turns[0],
            status=Payment.Status.PENDING,
        )
        self.client.force_login(self.member)

        response = self.client.post(
            reverse("review_payment", args=[self.jamiyah.pk, payment.pk]),
            {"action": "verify"},
        )

        payment.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(payment.status, Payment.Status.PENDING)

    def test_invalid_review_action_leaves_payment_pending(self):
        payment = Payment.objects.create(
            jamiyah=self.jamiyah,
            membership=self.member_membership,
            payout_turn=self.turns[0],
            status=Payment.Status.PENDING,
        )
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("review_payment", args=[self.jamiyah.pk, payment.pk]),
            {"action": "invalid"},
        )
        payment.refresh_from_db()

        self.assertRedirects(response, reverse("payment_dashboard", args=[self.jamiyah.pk]))
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertIsNone(payment.reviewed_by)
        self.assertIsNone(payment.reviewed_at)

    def test_payment_dashboard_requires_approved_membership(self):
        self.client.force_login(self.other)

        response = self.client.get(reverse("payment_dashboard", args=[self.jamiyah.pk]))

        self.assertEqual(response.status_code, 404)

    def test_payment_validation_rejects_cross_jamiyah_membership(self):
        other_manager = make_user("other_manager", 104)
        other_jamiyah = make_jamiyah(other_manager, name="Other Payment Jamiyah")
        other_membership = Membership.objects.get(
            jamiyah=other_jamiyah,
            user=other_manager,
        )
        payment = Payment(
            jamiyah=self.jamiyah,
            membership=other_membership,
            payout_turn=self.turns[0],
            status=Payment.Status.PENDING,
        )

        with self.assertRaises(ValidationError):
            payment.full_clean()

    def test_payment_save_rejects_cross_jamiyah_membership(self):
        other_manager = make_user("other_manager_save", 105)
        other_jamiyah = make_jamiyah(other_manager, name="Other Save Jamiyah")
        other_membership = Membership.objects.get(
            jamiyah=other_jamiyah,
            user=other_manager,
        )
        payment = Payment(
            jamiyah=self.jamiyah,
            membership=other_membership,
            payout_turn=self.turns[0],
            status=Payment.Status.PENDING,
        )

        with self.assertRaises(ValidationError):
            payment.save()
        self.assertFalse(
            Payment.objects.filter(
                jamiyah=self.jamiyah,
                membership=other_membership,
                payout_turn=self.turns[0],
            ).exists()
        )

    def test_payment_validation_rejects_cross_jamiyah_payout_turn(self):
        other_manager = make_user("turn_manager", 106)
        other_member = make_user("turn_member", 107)
        other_jamiyah = make_jamiyah(other_manager, name="Other Turn Jamiyah")
        other_manager_membership = Membership.objects.get(
            jamiyah=other_jamiyah,
            user=other_manager,
        )
        other_member_membership = add_membership(other_jamiyah, other_member)
        other_turn = activate_jamiyah(
            other_jamiyah,
            [other_manager_membership, other_member_membership],
        )[0]
        payment = Payment(
            jamiyah=self.jamiyah,
            membership=self.member_membership,
            payout_turn=other_turn,
            status=Payment.Status.PENDING,
        )

        with self.assertRaises(ValidationError):
            payment.full_clean()

    def test_duplicate_payment_record_is_rejected_by_database_constraint(self):
        Payment.objects.create(
            jamiyah=self.jamiyah,
            membership=self.member_membership,
            payout_turn=self.turns[0],
            status=Payment.Status.PENDING,
        )

        with self.assertRaises(IntegrityError):
            Payment.objects.create(
                jamiyah=self.jamiyah,
                membership=self.member_membership,
                payout_turn=self.turns[0],
                status=Payment.Status.PENDING,
            )


class DeliveryWorkflowTests(TestCase):
    def setUp(self):
        self.manager = make_user("delivery_manager", 201)
        self.member = make_user("delivery_member", 202)
        self.jamiyah = make_jamiyah(self.manager)
        self.manager_membership = Membership.objects.get(
            jamiyah=self.jamiyah,
            user=self.manager,
        )
        self.member_membership = add_membership(self.jamiyah, self.member)
        self.turns = activate_jamiyah(
            self.jamiyah,
            [self.manager_membership, self.member_membership],
        )

    def _verify_all_payments_for_turn(self, turn):
        for membership in [self.manager_membership, self.member_membership]:
            Payment.objects.create(
                jamiyah=self.jamiyah,
                membership=membership,
                payout_turn=turn,
                status=Payment.Status.VERIFIED,
                reviewed_by=self.manager,
            )

    def test_delivery_confirmation_requires_all_verified_payments(self):
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse(
                "confirm_payout_delivery",
                args=[self.jamiyah.pk, self.turns[0].pk],
            )
        )
        self.turns[0].refresh_from_db()

        self.assertRedirects(response, reverse("jamiyah_detail", args=[self.jamiyah.pk]))
        self.assertIsNone(self.turns[0].delivered_at)

    def test_manager_confirms_delivery_and_completion_after_final_turn(self):
        self.client.force_login(self.manager)

        self._verify_all_payments_for_turn(self.turns[0])
        first_response = self.client.post(
            reverse(
                "confirm_payout_delivery",
                args=[self.jamiyah.pk, self.turns[0].pk],
            )
        )
        self.turns[0].refresh_from_db()
        self.jamiyah.refresh_from_db()

        self._verify_all_payments_for_turn(self.turns[1])
        second_response = self.client.post(
            reverse(
                "confirm_payout_delivery",
                args=[self.jamiyah.pk, self.turns[1].pk],
            )
        )
        self.turns[1].refresh_from_db()
        self.jamiyah.refresh_from_db()

        self.assertRedirects(
            first_response,
            reverse("jamiyah_detail", args=[self.jamiyah.pk]),
        )
        self.assertIsNotNone(self.turns[0].delivered_at)
        self.assertEqual(self.turns[0].delivered_by, self.manager)
        self.assertEqual(self.jamiyah.status, Jamiyah.Status.COMPLETED)
        self.assertRedirects(
            second_response,
            reverse("jamiyah_detail", args=[self.jamiyah.pk]),
        )
        self.assertIsNotNone(self.turns[1].delivered_at)
        self.assertIsNotNone(self.jamiyah.completed_at)

    def test_non_manager_cannot_confirm_delivery(self):
        self._verify_all_payments_for_turn(self.turns[0])
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "confirm_payout_delivery",
                args=[self.jamiyah.pk, self.turns[0].pk],
            )
        )
        self.turns[0].refresh_from_db()

        self.assertEqual(response.status_code, 404)
        self.assertIsNone(self.turns[0].delivered_at)

    def test_later_turn_cannot_be_delivered_before_previous_turn(self):
        self._verify_all_payments_for_turn(self.turns[1])
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse(
                "confirm_payout_delivery",
                args=[self.jamiyah.pk, self.turns[1].pk],
            )
        )
        self.turns[1].refresh_from_db()
        self.jamiyah.refresh_from_db()

        self.assertRedirects(response, reverse("jamiyah_detail", args=[self.jamiyah.pk]))
        self.assertIsNone(self.turns[1].delivered_at)
        self.assertEqual(self.jamiyah.status, Jamiyah.Status.ACTIVE)
