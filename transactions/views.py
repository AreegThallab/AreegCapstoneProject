from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from django.http import Http404
from django.utils import timezone

from jamiyahs.models import Jamiyah, Membership, PayoutTurn
from .models import Payment


# =========================================
# 01. PAYMENT DASHBOARD
# =========================================

@login_required
def payment_dashboard(request, pk):

    jamiyah = get_object_or_404(Jamiyah, pk=pk)

    my_membership = get_object_or_404(
        Membership,
        jamiyah=jamiyah,
        user=request.user,
        status=Membership.Status.APPROVED
    )

    is_manager = (
        my_membership.role == Membership.Role.MANAGER
    )

    payout_turns = list(
        PayoutTurn.objects
        .filter(jamiyah=jamiyah)
        .select_related("membership__user")
        .order_by("position")
    )

    members = list(
        Membership.objects
        .filter(
            jamiyah=jamiyah,
            status=Membership.Status.APPROVED
        )
        .select_related("user", "user__profile")
        .order_by("joined_at")
    )

    payments = Payment.objects.filter(
        jamiyah=jamiyah
    ).select_related(
        "membership",
        "payout_turn"
    )

    payment_lookup = {
        (payment.membership_id, payment.payout_turn_id): payment
        for payment in payments
    }

    # Manager sees all members.
    # Regular member sees only their own payments.
    visible_members = (
        members if is_manager else [my_membership]
    )

    rounds = []

    for turn in payout_turns:

        rows = []
        verified_count = 0

        for membership in members:

            payment = payment_lookup.get(
                (membership.pk, turn.pk)
            )

            if payment and payment.status == Payment.Status.VERIFIED:
                verified_count += 1

            if membership in visible_members:
                rows.append({
                    "membership": membership,
                    "payment": payment,
                    "can_report": (
                        membership.pk == my_membership.pk
                        and jamiyah.status == Jamiyah.Status.ACTIVE
                        and (
                            payment is None
                            or payment.status == Payment.Status.REJECTED
                        )
                    ),
                })

        rounds.append({
            "turn": turn,
            "rows": rows,
            "verified_count": verified_count,
            "total_members": len(members),
            "is_complete": (
                len(members) > 0
                and verified_count == len(members)
            ),
        })

    context = {
        "jamiyah": jamiyah,
        "my_membership": my_membership,
        "is_manager": is_manager,
        "rounds": rounds,
        "members_count": len(members),
    }

    return render(
        request,
        "transactions/payments.html",
        context
    )


# =========================================
# 02. MEMBER REPORTS PAYMENT
# =========================================

@login_required
@require_POST
def report_payment(request, pk, turn_id):

    with transaction.atomic():

        jamiyah = get_object_or_404(
            Jamiyah,
            pk=pk
        )

        membership = get_object_or_404(
            Membership,
            jamiyah=jamiyah,
            user=request.user,
            status=Membership.Status.APPROVED
        )

        if jamiyah.status != Jamiyah.Status.ACTIVE:
            messages.error(
                request,
                "تسجيل الدفعات متاح للجمعيات الجارية فقط."
            )
            return redirect("payment_dashboard", pk=pk)

        turn = get_object_or_404(
            PayoutTurn,
            pk=turn_id,
            jamiyah=jamiyah
        )

        payment, created = Payment.objects.get_or_create(
            jamiyah=jamiyah,
            membership=membership,
            payout_turn=turn,
            defaults={
                "status": Payment.Status.PENDING
            }
        )

        if not created:

            if payment.status == Payment.Status.VERIFIED:
                messages.warning(
                    request,
                    "هذه الدفعة مؤكدة بالفعل."
                )

            elif payment.status == Payment.Status.PENDING:
                messages.warning(
                    request,
                    "بلاغ هذه الدفعة بانتظار تأكيد المدير."
                )

            else:
                # Allow resubmitting a rejected report.
                payment.status = Payment.Status.PENDING
                payment.reported_at = timezone.now()
                payment.reviewed_by = None
                payment.reviewed_at = None

                payment.full_clean()
                payment.save(
                    update_fields=[
                        "status",
                        "reported_at",
                        "reviewed_by",
                        "reviewed_at",
                    ]
                )

                messages.success(
                    request,
                    "تمت إعادة إرسال بلاغ الدفعة للمراجعة."
                )

        else:
            messages.success(
                request,
                "تم تسجيل بلاغ الدفعة وبانتظار تأكيد المدير."
            )

    return redirect("payment_dashboard", pk=pk)


# =========================================
# 03. MANAGER REVIEWS PAYMENT
# =========================================

@login_required
@require_POST
def review_payment(request, pk, payment_id):

    with transaction.atomic():

        jamiyah = get_object_or_404(
            Jamiyah,
            pk=pk
        )

        is_manager = Membership.objects.filter(
            jamiyah=jamiyah,
            user=request.user,
            role=Membership.Role.MANAGER,
            status=Membership.Status.APPROVED
        ).exists()

        if not is_manager:
            raise Http404("غير مسموح.")

        if jamiyah.status != Jamiyah.Status.ACTIVE:
            messages.error(
                request,
                "مراجعة الدفعات متاحة للجمعيات الجارية فقط."
            )
            return redirect("payment_dashboard", pk=pk)

        payment = get_object_or_404(
            Payment,
            pk=payment_id,
            jamiyah=jamiyah,
            status=Payment.Status.PENDING
        )

        action = request.POST.get("action")

        if action == "verify":
            payment.status = Payment.Status.VERIFIED
            success_message = "تم تأكيد الدفعة بنجاح."

        elif action == "reject":
            payment.status = Payment.Status.REJECTED
            success_message = "تم رفض بلاغ الدفعة."

        else:
            messages.error(
                request,
                "الإجراء غير صالح."
            )
            return redirect("payment_dashboard", pk=pk)

        payment.reviewed_by = request.user
        payment.reviewed_at = timezone.now()

        payment.full_clean()
        payment.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
            ]
        )

    messages.success(
        request,
        success_message
    )

    return redirect("payment_dashboard", pk=pk)
