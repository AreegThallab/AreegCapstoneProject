from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from jamiyahs.models import Jamiyah, Membership, PayoutTurn


# =========================================
# PAYMENT MODEL
# =========================================

class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "بانتظار التأكيد"
        VERIFIED = "verified", "مؤكدة"
        REJECTED = "rejected", "مرفوضة"

    jamiyah = models.ForeignKey(
        Jamiyah,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    membership = models.ForeignKey(
        Membership,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    # The round this payment belongs to
    payout_turn = models.ForeignKey(
        PayoutTurn,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )

    # When the member reported payment
    reported_at = models.DateTimeField(
        auto_now_add=True
    )

    # Manager who confirmed or rejected it
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_payments"
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-reported_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["membership", "payout_turn"],
                name="unique_member_payment_per_round"
            )
        ]

    def clean(self):
        super().clean()

        if self.membership_id:
            if self.membership.jamiyah_id != self.jamiyah_id:
                raise ValidationError(
                    "العضوية لا تتبع هذه الجمعية."
                )

            if self.membership.status != Membership.Status.APPROVED:
                raise ValidationError(
                    "لا يمكن توثيق دفعة لعضو غير مقبول."
                )

        if self.payout_turn_id:
            if self.payout_turn.jamiyah_id != self.jamiyah_id:
                raise ValidationError(
                    "الدورة لا تتبع هذه الجمعية."
                )

    def __str__(self):
        return (
            f"{self.membership.user.username} - "
            f"{self.jamiyah.name} - "
            f"الدورة {self.payout_turn.position}"
        )
