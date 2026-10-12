from django.test import TestCase
from django.urls import reverse

from jamiyahs.models import Jamiyah, Membership
from jamiyahs.tests import add_membership, make_jamiyah, make_user
from transactions.models import Payment
from transactions.tests import activate_jamiyah


class ReportsAggregationAnnotationTests(TestCase):
    def setUp(self):
        self.manager = make_user("report_manager", 301)
        self.member = make_user("report_member", 302)
        self.outsider = make_user("report_outsider", 303)
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

        Payment.objects.create(
            jamiyah=self.jamiyah,
            membership=self.manager_membership,
            payout_turn=self.turns[0],
            status=Payment.Status.VERIFIED,
            reviewed_by=self.manager,
        )
        Payment.objects.create(
            jamiyah=self.jamiyah,
            membership=self.member_membership,
            payout_turn=self.turns[0],
            status=Payment.Status.VERIFIED,
            reviewed_by=self.manager,
        )
        Payment.objects.create(
            jamiyah=self.jamiyah,
            membership=self.manager_membership,
            payout_turn=self.turns[1],
            status=Payment.Status.PENDING,
        )
        Payment.objects.create(
            jamiyah=self.jamiyah,
            membership=self.member_membership,
            payout_turn=self.turns[1],
            status=Payment.Status.REJECTED,
            reviewed_by=self.manager,
        )
        self.turns[0].delivered_by = self.manager
        self.turns[0].delivered_at = self.jamiyah.created_at
        self.turns[0].save(update_fields=["delivered_by", "delivered_at"])

    def test_reports_dashboard_aggregates_user_memberships_and_payments(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse("reports_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_jamiyahs"], 1)
        self.assertEqual(response.context["active_count"], 1)
        self.assertEqual(response.context["verified_count"], 1)
        self.assertEqual(response.context["pending_count"], 1)
        self.assertEqual(response.context["rejected_count"], 0)
        self.assertEqual(response.context["verified_amount"], self.jamiyah.contribution_amount)
        self.assertEqual(response.context["delivered_count"], 1)
        self.assertEqual(
            response.context["delivered_amount"],
            self.jamiyah.contribution_amount * self.jamiyah.max_members,
        )

    def test_jamiyah_report_aggregates_all_payment_statuses(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse("jamiyah_report", args=[self.jamiyah.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["approved_count"], 2)
        self.assertEqual(response.context["verified_count"], 2)
        self.assertEqual(response.context["pending_count"], 1)
        self.assertEqual(response.context["rejected_count"], 1)
        self.assertEqual(
            response.context["verified_amount"],
            self.jamiyah.contribution_amount * 2,
        )
        self.assertEqual(response.context["delivered_count"], 1)
        self.assertEqual(len(response.context["report_rows"]), 2)
        first_row = response.context["report_rows"][0]
        self.assertEqual(first_row["verified_count"], 2)
        self.assertEqual(first_row["required_count"], 2)
        self.assertTrue(first_row["is_delivered"])

    def test_jamiyah_report_requires_approved_membership(self):
        self.client.force_login(self.outsider)

        response = self.client.get(reverse("jamiyah_report", args=[self.jamiyah.pk]))

        self.assertEqual(response.status_code, 404)

    def test_explore_annotates_approved_member_count(self):
        self.client.force_login(self.outsider)

        response = self.client.get(reverse("explore_jamiyahs"))

        self.assertEqual(response.status_code, 200)
        jamiyahs = response.context["jamiyahs"]
        self.assertEqual(len(jamiyahs), 1)
        self.assertEqual(jamiyahs[0].approved_count, 2)
        self.assertEqual(jamiyahs[0].remaining_seats, 0)
