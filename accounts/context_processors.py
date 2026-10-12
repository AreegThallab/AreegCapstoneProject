
from jamiyahs.models import Jamiyah, Membership, PayoutTurn
from transactions.models import Payment


# =========================================
# DASHBOARD NOTIFICATIONS
# =========================================
def dashboard_notifications(request):
    if not request.user.is_authenticated:
        return {
            "notification_count": 0,
            "pending_join_notifications": [],
            "pending_payment_notifications": [],
            "membership_updates": [],
            "payment_updates": [],
            "delivery_notifications": [],
            "completion_notifications": [],
        }

    user = request.user

    # 01. MANAGER'S JAMIYAHS
    managed_jamiyah_ids = Membership.objects.filter(
        user=user,
        role=Membership.Role.MANAGER,
        status=Membership.Status.APPROVED
    ).values_list("jamiyah_id", flat=True)

    # 02. PENDING JOIN REQUESTS
    pending_joins = Membership.objects.filter(
        jamiyah_id__in=managed_jamiyah_ids,
        status=Membership.Status.PENDING
    ).select_related(
        "user",
        "jamiyah"
    ).order_by("-joined_at")

    # 03. PENDING PAYMENTS
    pending_payments = Payment.objects.filter(
        jamiyah_id__in=managed_jamiyah_ids,
        status=Payment.Status.PENDING
    ).select_related(
        "jamiyah",
        "membership__user",
        "payout_turn"
    ).order_by("-reported_at")

    # 04. MEMBERSHIP UPDATES
    membership_updates = Membership.objects.filter(
        user=user,
        role=Membership.Role.MEMBER,
        status__in=[
            Membership.Status.APPROVED,
            Membership.Status.REJECTED
        ]
    ).select_related("jamiyah").order_by("-joined_at")[:5]

    # 05. PAYMENT UPDATES
    payment_updates = Payment.objects.filter(
        membership__user=user,
        status__in=[
            Payment.Status.VERIFIED,
            Payment.Status.REJECTED
        ]
    ).select_related(
        "jamiyah",
        "payout_turn"
    ).order_by("-reviewed_at")[:5]

    # 06. PAYOUT DELIVERY NOTIFICATIONS
    unread_deliveries = PayoutTurn.objects.filter(
        membership__user=user,
        membership__status=Membership.Status.APPROVED,
        delivered_at__isnull=False,
        recipient_seen_at__isnull=True
    ).select_related(
        "jamiyah",
        "delivered_by"
    ).order_by("-delivered_at")

    # 07. COMPLETED JAMIYAH NOTIFICATIONS
    unread_completions = Membership.objects.filter(
        user=user,
        status=Membership.Status.APPROVED,
        completion_seen_at__isnull=True,
        jamiyah__status=Jamiyah.Status.COMPLETED,
        jamiyah__completed_at__isnull=False
    ).select_related(
        "jamiyah"
    ).order_by("-jamiyah__completed_at")

    # 08. UNREAD NOTIFICATION COUNT
    notification_count = (
        pending_joins.count()
        + pending_payments.count()
        + unread_deliveries.count()
        + unread_completions.count()
    )

    return {
        "notification_count": notification_count,
        "pending_join_notifications": pending_joins[:5],
        "pending_payment_notifications": pending_payments[:5],
        "membership_updates": membership_updates,
        "payment_updates": payment_updates,
        "delivery_notifications": unread_deliveries[:5],
        "completion_notifications": unread_completions[:5],
    }
