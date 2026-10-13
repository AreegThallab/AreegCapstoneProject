
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


# =========================================
# 01. JAMIYAH MODEL
# =========================================

class Jamiyah(models.Model):

    # Visibility choices
    class Visibility(models.TextChoices):
        PUBLIC = "public", "عامة"
        PRIVATE = "private", "خاصة"

    # Jamiyah status choices
    class Status(models.TextChoices):
        OPEN = "open", "مفتوحة للانضمام"
        ACTIVE = "active", "جارية"
        COMPLETED = "completed", "مكتملة"
        CANCELLED = "cancelled", "ملغاة"

    # Contribution frequency choices
    class Frequency(models.TextChoices):
        WEEKLY = "weekly", "أسبوعية"
        MONTHLY = "monthly", "شهرية"

    name = models.CharField(
        max_length=150
    )

    description = models.TextField(
        blank=True
    )

    creator = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_jamiyahs"
    )

    contribution_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(1)
        ]
    )

    max_members = models.PositiveIntegerField(
        validators=[
            MinValueValidator(2)
        ]
    )

    # Weekly or monthly
    frequency = models.CharField(
        max_length=10,
        choices=Frequency.choices,
        default=Frequency.MONTHLY
    )

    # Null allowed for previously created Jamiyahs
    start_date = models.DateField(
        null=True,
        blank=True
    )

    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PRIVATE
    )

    # Private invitation token
    invite_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    # Date when all payout turns were delivered
    completed_at = models.DateTimeField(
    null=True,
    blank=True
    )

    class Meta:
        ordering = [
            "-created_at"
        ]

    def __str__(self):
        return self.name


# =========================================
# 02. MEMBERSHIP MODEL
# =========================================

class Membership(models.Model):

    # Membership roles
    class Role(models.TextChoices):
        MANAGER = "manager", "مدير"
        MEMBER = "member", "عضو"

    # Membership statuses
    class Status(models.TextChoices):
        PENDING = "pending", "بانتظار الموافقة"
        APPROVED = "approved", "مقبول"
        REJECTED = "rejected", "مرفوض"

    jamiyah = models.ForeignKey(
        Jamiyah,
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="jamiyah_memberships"
    )

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )
    # When the member read the completion notification
    completion_seen_at = models.DateTimeField(
    null=True,
    blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "jamiyah",
                    "user"
                ],
                name="unique_jamiyah_membership"
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.jamiyah.name}"
        )


# =========================================
# 03. PAYOUT TURN MODEL
# =========================================

class PayoutTurn(models.Model):

    # The Jamiyah this turn belongs to
    jamiyah = models.ForeignKey(
        Jamiyah,
        on_delete=models.CASCADE,
        related_name="payout_turns"
    )

    # One payout turn per membership
    membership = models.OneToOneField(
        Membership,
        on_delete=models.CASCADE,
        related_name="payout_turn"
    )

    # Order of receiving the payout
    position = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1)
        ]
    )

    # Scheduled payout date
    payout_date = models.DateField()

    # Date and time the manager confirmed delivery
    delivered_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Manager who confirmed delivery
    delivered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_payout_deliveries"
    )

    # Date and time the recipient marked the notification as read
    recipient_seen_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = [
            "position"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "jamiyah",
                    "position"
                ],
                name="unique_payout_position"
            )
        ]

    def clean(self):
        super().clean()

        if self.membership_id:

            # Membership must belong to the same Jamiyah
            if self.jamiyah_id != self.membership.jamiyah_id:
                raise ValidationError(
                    "العضوية لا تتبع هذه الجمعية."
                )

            # Only approved members can have a payout turn
            if self.membership.status != Membership.Status.APPROVED:
                raise ValidationError(
                    "لا يمكن تحديد دور لعضو غير مقبول."
                )

    def save(self, *args, **kwargs):
        self.full_clean(
            validate_unique=False,
            validate_constraints=False
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.jamiyah.name} - "
            f"الدور {self.position}"
        )
