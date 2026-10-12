
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.db.models import Count, Q

from jamiyahs.models import Jamiyah, Membership, PayoutTurn
from transactions.models import Payment


# =========================================
# 01. REPORTS DASHBOARD
# =========================================

@login_required
def reports_dashboard(request):

    # Approved Jamiyahs for the current user
    memberships = (
        Membership.objects
        .filter(
            user=request.user,
            status=Membership.Status.APPROVED
        )
        .select_related("jamiyah")
        .order_by("-jamiyah__created_at")
    )

    jamiyahs = [
        membership.jamiyah
        for membership in memberships
    ]

    jamiyah_ids = [
        jamiyah.pk
        for jamiyah in jamiyahs
    ]

    # =====================================
    # JAMIYAH STATISTICS
    # =====================================

    open_count = sum(
        1
        for jamiyah in jamiyahs
        if jamiyah.status == Jamiyah.Status.OPEN
    )

    active_count = sum(
        1
        for jamiyah in jamiyahs
        if jamiyah.status == Jamiyah.Status.ACTIVE
    )

    completed_count = sum(
        1
        for jamiyah in jamiyahs
        if jamiyah.status == Jamiyah.Status.COMPLETED
    )

    # =====================================
    # USER PAYMENT STATISTICS
    # =====================================

    payments = Payment.objects.filter(
        membership__user=request.user,
        jamiyah_id__in=jamiyah_ids
    ).select_related("jamiyah")

    verified_payments = payments.filter(
        status=Payment.Status.VERIFIED
    )

    verified_count = verified_payments.count()

    pending_count = payments.filter(
        status=Payment.Status.PENDING
    ).count()

    rejected_count = payments.filter(
        status=Payment.Status.REJECTED
    ).count()

    verified_amount = sum(
        (
            payment.jamiyah.contribution_amount
            for payment in verified_payments
        ),
        Decimal("0.00")
    )

    # =====================================
    # CONFIRMED PAYOUT DELIVERIES
    # =====================================

    delivered_turns = (
        PayoutTurn.objects
        .filter(
            jamiyah_id__in=jamiyah_ids,
            delivered_at__isnull=False
        )
        .select_related("jamiyah")
    )

    delivered_count = 0
    delivered_amount = Decimal("0.00")

    for turn in delivered_turns:
        delivered_count += 1

        delivered_amount += (
            turn.jamiyah.contribution_amount
            * turn.jamiyah.max_members
        )

    # =====================================
    # TEMPLATE CONTEXT
    # =====================================

    context = {
        "total_jamiyahs": len(jamiyahs),
        "open_count": open_count,
        "active_count": active_count,
        "completed_count": completed_count,
        "verified_count": verified_count,
        "pending_count": pending_count,
        "rejected_count": rejected_count,
        "verified_amount": verified_amount,
        "delivered_count": delivered_count,
        "delivered_amount": delivered_amount,
        "memberships": memberships,
    }

    return render(
        request,
        "reports/dashboard.html",
        context
    )


# =========================================
# 02. JAMIYAH DETAIL REPORT
# =========================================

@login_required
def jamiyah_report(request, pk):

    # =====================================
    # JAMIYAH AND ACCESS PERMISSIONS
    # =====================================

    jamiyah = get_object_or_404(
        Jamiyah,
        pk=pk
    )

    membership = (
        Membership.objects
        .filter(
            jamiyah=jamiyah,
            user=request.user,
            status=Membership.Status.APPROVED
        )
        .first()
    )

    if membership is None:
        raise Http404(
            "هذا التقرير متاح لأعضاء الجمعية فقط."
        )

    # =====================================
    # APPROVED MEMBERS
    # =====================================

    approved_count = Membership.objects.filter(
        jamiyah=jamiyah,
        status=Membership.Status.APPROVED
    ).count()

    # =====================================
    # PAYMENT STATISTICS
    # =====================================

    payments = Payment.objects.filter(
        jamiyah=jamiyah
    )

    payment_counts = payments.aggregate(
        verified=Count(
            "id",
            filter=Q(status=Payment.Status.VERIFIED)
        ),
        pending=Count(
            "id",
            filter=Q(status=Payment.Status.PENDING)
        ),
        rejected=Count(
            "id",
            filter=Q(status=Payment.Status.REJECTED)
        )
    )

    verified_count = payment_counts["verified"]
    pending_count = payment_counts["pending"]
    rejected_count = payment_counts["rejected"]

    verified_amount = (
        jamiyah.contribution_amount
        * verified_count
    )

    # Total payout amount for each turn
    payout_amount = (
        jamiyah.contribution_amount
        * jamiyah.max_members
    )

    # =====================================
    # PAYOUT TURNS
    # =====================================

    turns = list(
        PayoutTurn.objects
        .filter(jamiyah=jamiyah)
        .select_related(
            "membership__user",
            "membership__user__profile",
            "delivered_by"
        )
        .order_by("position")
    )

    # Get all payment statuses in one query
    verified_payments_by_turn = {
        item["payout_turn_id"]: item["total"]
        for item in (
            payments
            .filter(status=Payment.Status.VERIFIED)
            .values("payout_turn_id")
            .annotate(total=Count("id"))
        )
    }

    # =====================================
    # BUILD REPORT ROWS
    # =====================================

    report_rows = []
    delivered_count = 0

    for turn in turns:

        turn_verified_count = (
            verified_payments_by_turn.get(
                turn.pk,
                0
            )
        )

        is_delivered = turn.delivered_at is not None

        if is_delivered:
            delivered_count += 1

        # Full name when available
        user = turn.membership.user

        try:
            recipient_name = (
                user.profile.full_name
                or user.username
            )
        except AttributeError:
            recipient_name = user.username

        report_rows.append({
            "position": turn.position,
            "recipient_name": recipient_name,
            "payout_date": turn.payout_date,
            "verified_count": turn_verified_count,
            "required_count": approved_count,
            "amount": payout_amount,
            "is_delivered": is_delivered,
            "delivered_at": turn.delivered_at,
            "delivered_by": turn.delivered_by,
        })

    # =====================================
    # DELIVERED AMOUNT
    # =====================================

    delivered_amount = (
        payout_amount
        * delivered_count
    )

    # =====================================
    # TEMPLATE CONTEXT
    # =====================================

    context = {
        "jamiyah": jamiyah,
        "membership": membership,
        "approved_count": approved_count,

        "verified_count": verified_count,
        "pending_count": pending_count,
        "rejected_count": rejected_count,
        "verified_amount": verified_amount,

        "payout_amount": payout_amount,
        "delivered_count": delivered_count,
        "delivered_amount": delivered_amount,

        "report_rows": report_rows,
    }

    return render(
        request,
        "reports/jamiyah_report.html",
        context
    )
