import calendar
import uuid
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from transactions.models import Payment
from .forms import JamiyahForm
from .models import Jamiyah, Membership, PayoutTurn

# =========================================
# 01. CREATE JAMIYAH

# =========================================
@login_required
def create_jamiyah(request):
    if request.method == "POST":
        form = JamiyahForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                jamiyah = form.save(commit=False)
                jamiyah.creator = request.user
                jamiyah.save()
                # Creator becomes the first approved member
                Membership.objects.create(
                    jamiyah=jamiyah,
                    user=request.user,
                    role=Membership.Role.MANAGER,
                    status=Membership.Status.APPROVED
                )
            messages.success(
                request,
                "تم إنشاء الجمعية بنجاح!"
            )
            return redirect(
                "jamiyah_detail",
                pk=jamiyah.pk
            )
    else:
        form = JamiyahForm()
    return render(
        request,
        "jamiyahs/create.html",
        {"form": form}
    )

# =========================================
# 02. MY JAMIYAHS

# =========================================
@login_required
def my_jamiyahs(request):
    memberships = (
        Membership.objects
        .filter(
            user=request.user,
            status=Membership.Status.APPROVED
        )
        .select_related("jamiyah")
        .order_by("-joined_at")
    )
    total_jamiyahs = memberships.count()
    managed_jamiyahs = memberships.filter(
        role=Membership.Role.MANAGER
    ).count()
    joined_jamiyahs = memberships.filter(
        role=Membership.Role.MEMBER
    ).count()
    selected_filter = request.GET.get(
        "filter",
        "all"
    )
    if selected_filter not in ("all", "managed", "joined"):
        selected_filter = "all"
    if selected_filter == "managed":
        memberships = memberships.filter(
            role=Membership.Role.MANAGER
        )
    elif selected_filter == "joined":
        memberships = memberships.filter(
            role=Membership.Role.MEMBER
        )
    context = {
        "memberships": memberships,
        "selected_filter": selected_filter,
        "total_jamiyahs": total_jamiyahs,
        "managed_jamiyahs": managed_jamiyahs,
        "joined_jamiyahs": joined_jamiyahs,
    }
    return render(
        request,
        "jamiyahs/my_jamiyahs.html",
        context
    )

# =========================================
# 03. JAMIYAH DETAIL

# =========================================
@login_required
def jamiyah_detail(request, pk):
    # Get the requested Jamiyah
    jamiyah = get_object_or_404(
        Jamiyah.objects.select_related("creator"),
        pk=pk
    )
    # Get current user's membership
    my_membership = Membership.objects.filter(
        jamiyah=jamiyah,
        user=request.user
    ).first()
    is_approved = (
        my_membership is not None
        and my_membership.status == Membership.Status.APPROVED
    )
    is_manager = (
        is_approved
        and my_membership.role == Membership.Role.MANAGER
    )
    # Private Jamiyahs remain accessible
    # only to approved members.
    if (
        jamiyah.visibility == Jamiyah.Visibility.PRIVATE
        and not is_approved
    ):
        raise Http404("الجمعية غير متاحة.")
    # All approved memberships.
    # Keep this queryset for payout scheduling.
    members = (
        Membership.objects
        .filter(
            jamiyah=jamiyah,
            status=Membership.Status.APPROVED
        )
        .select_related("user", "user__profile")
        .order_by("joined_at")
    )
    approved_count = members.count()
    remaining_seats = max(
        jamiyah.max_members - approved_count,
        0
    )
    # -------------------------------------
    # NEW: SEPARATE MANAGER AND MEMBERS
    # -------------------------------------
    # Manager is displayed in a separate card.
    manager_membership = members.filter(
        role=Membership.Role.MANAGER
    ).first()
    # Regular members exclude the manager.
    regular_members = members.filter(
        role=Membership.Role.MEMBER
    )
    # -------------------------------------
    # MANAGER JOIN REQUESTS
    # -------------------------------------
    pending_requests = Membership.objects.none()
    if is_manager:
        pending_requests = (
            Membership.objects
            .filter(
                jamiyah=jamiyah,
                status=Membership.Status.PENDING
            )
            .select_related("user", "user__profile")
            .order_by("joined_at")
        )
    # Public Jamiyahs accept join requests
    # if they are open and have seats.
    can_request_join = (
        jamiyah.visibility == Jamiyah.Visibility.PUBLIC
        and jamiyah.status == Jamiyah.Status.OPEN
        and remaining_seats > 0
        and my_membership is None
    )
    # -------------------------------------
    # PAYOUT SCHEDULE
    # -------------------------------------
    payout_turns = (
        PayoutTurn.objects
        .filter(jamiyah=jamiyah)
        .select_related(
            "membership__user",
            "membership__user__profile"
        )
        .order_by("position")
    )
    # One query for the payment statuses of all scheduled turns.
    all_payments = Payment.objects.filter(
        jamiyah=jamiyah,
        payout_turn__in=payout_turns
    ).select_related("membership")
    payments_map = {
        (payment.payout_turn_id, payment.membership_id): payment
        for payment in all_payments
    }
    member_list = list(members)
    required_count = len(member_list)
    payout_amount = jamiyah.contribution_amount * jamiyah.max_members
    timeline_rows = []
    delivered_turns_count = 0
    for turn in payout_turns:
        verified_count = 0
        payment_members = []
        for member in member_list:
            payment = payments_map.get((turn.pk, member.pk))
            payment_status = payment.status if payment else "missing"
            if payment_status == Payment.Status.VERIFIED:
                verified_count += 1
            payment_members.append({
                "membership": member,
                "payment_status": payment_status,
            })
        if turn.delivered_at:
            delivered_turns_count += 1
        ready_to_deliver = (
            jamiyah.status == Jamiyah.Status.ACTIVE
            and required_count == jamiyah.max_members
            and verified_count == required_count
            and not turn.delivered_at
        )
        timeline_rows.append({
            "turn": turn,
            "verified_count": verified_count,
            "required_count": required_count,
            "payment_members": payment_members,
            "payout_amount": payout_amount,
            "ready_to_deliver": ready_to_deliver,
            "is_recipient": my_membership is not None
            and turn.membership_id == my_membership.pk,
        })
    can_generate_schedule = (
        is_manager
        and jamiyah.status == Jamiyah.Status.OPEN
        and approved_count == jamiyah.max_members
        and jamiyah.start_date is not None
        and not payout_turns.exists()
    )
    invite_url = None
    if is_manager and jamiyah.visibility == Jamiyah.Visibility.PRIVATE:
        invite_url = request.build_absolute_uri(
            reverse("private_jamiyah_invite", kwargs={"token": jamiyah.invite_token})
        )
    context = {
        "jamiyah": jamiyah,
        "my_membership": my_membership,
        "is_approved": is_approved,
        "is_manager": is_manager,
        # Original queryset: used in payout form
        "members": members,
        # New: separate lists for the UI
        "manager_membership": manager_membership,
        "regular_members": regular_members,
        "approved_count": approved_count,
        "remaining_seats": remaining_seats,
        "pending_requests": pending_requests,
        "can_request_join": can_request_join,
        "payout_turns": payout_turns,
        "timeline_rows": timeline_rows,
        "delivered_turns_count": delivered_turns_count,
        "can_generate_schedule": can_generate_schedule,
        "invite_url": invite_url,
        "today": timezone.localdate(),
    }
    return render(
        request,
        "jamiyahs/detail.html",
        context
    )

# =========================================
# 04. REQUEST TO JOIN

# =========================================
@login_required
@require_POST
def request_join(request, pk):
    with transaction.atomic():
        jamiyah = get_object_or_404(
            Jamiyah,
            pk=pk
        )
        if (
            jamiyah.visibility != Jamiyah.Visibility.PUBLIC
            or jamiyah.status != Jamiyah.Status.OPEN
        ):
            messages.error(
                request,
                "هذه الجمعية لا تستقبل طلبات انضمام عامة."
            )
            return redirect("my_jamiyahs")
        existing = Membership.objects.filter(
            jamiyah=jamiyah,
            user=request.user
        ).first()
        if existing:
            messages.warning(
                request,
                "لديك طلب أو عضوية مسجلة في هذه الجمعية."
            )
            return redirect("jamiyah_detail", pk=pk)
        member_count = Membership.objects.filter(
            jamiyah=jamiyah,
            status=Membership.Status.APPROVED
        ).count()
        if member_count >= jamiyah.max_members:
            messages.error(
                request,
                "اكتمل عدد أعضاء الجمعية."
            )
            return redirect("jamiyah_detail", pk=pk)
        Membership.objects.create(
            jamiyah=jamiyah,
            user=request.user,
            role=Membership.Role.MEMBER,
            status=Membership.Status.PENDING
        )
    messages.success(
        request,
        "تم إرسال طلب الانضمام، وبانتظار موافقة المدير."
    )
    return redirect(
        "jamiyah_detail",
        pk=pk
    )

# =========================================
# 05. MANAGE JOIN REQUEST

# =========================================
@login_required
@require_POST
def manage_join_request(request, pk, membership_id):
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
        membership = get_object_or_404(
            Membership,
            pk=membership_id,
            jamiyah=jamiyah,
            status=Membership.Status.PENDING,
            role=Membership.Role.MEMBER
        )
        action = request.POST.get("action")
        if action == "approve":
            if jamiyah.status != Jamiyah.Status.OPEN:
                messages.error(
                    request,
                    "الجمعية لا تستقبل أعضاء جدد حاليًا."
                )
            else:
                approved_count = Membership.objects.filter(
                    jamiyah=jamiyah,
                    status=Membership.Status.APPROVED
                ).count()
                if approved_count >= jamiyah.max_members:
                    messages.error(
                        request,
                        "اكتمل عدد أعضاء الجمعية."
                    )
                else:
                    membership.status = Membership.Status.APPROVED
                    membership.save(
                        update_fields=["status"]
                    )
                    messages.success(
                        request,
                        "تم قبول طلب الانضمام."
                    )
        elif action == "reject":
            membership.status = Membership.Status.REJECTED
            membership.save(
                update_fields=["status"]
            )
            messages.success(
                request,
                "تم رفض طلب الانضمام."
            )
        else:
            messages.error(
                request,
                "إجراء غير صالح."
            )
    return redirect(
        "jamiyah_detail",
        pk=pk
    )

# =========================================
# 06. EXPLORE PUBLIC JAMIYAHS

# =========================================
@login_required
def explore_jamiyahs(request):
    query = request.GET.get("q", "").strip()[:150]
    selected_status = request.GET.get("status", "all")

    allowed_statuses = {
        "all",
        Jamiyah.Status.OPEN,
        Jamiyah.Status.ACTIVE,
        Jamiyah.Status.COMPLETED,
    }
    if selected_status not in allowed_statuses:
        selected_status = "all"

    jamiyahs_qs = (
        Jamiyah.objects
        .filter(visibility=Jamiyah.Visibility.PUBLIC)
        .annotate(
            approved_count=Count(
                "memberships",
                filter=Q(
                    memberships__status=Membership.Status.APPROVED
                ),
                distinct=True
            )
        )
        .order_by("-created_at")
    )

    if query:
        jamiyahs_qs = jamiyahs_qs.filter(name__icontains=query)

    if selected_status != "all":
        jamiyahs_qs = jamiyahs_qs.filter(status=selected_status)

    jamiyahs = list(jamiyahs_qs)
    membership_map = {
        membership.jamiyah_id: membership
        for membership in Membership.objects.filter(
            user=request.user,
            jamiyah_id__in=[jamiyah.pk for jamiyah in jamiyahs]
        )
    }

    for jamiyah in jamiyahs:
        jamiyah.remaining_seats = max(
            jamiyah.max_members - jamiyah.approved_count,
            0
        )
        jamiyah.viewer_membership = membership_map.get(jamiyah.pk)

    return render(
        request,
        "jamiyahs/explore.html",
        {
            "jamiyahs": jamiyahs,
            "query": query,
            "selected_status": selected_status,
        }
    )

# =========================================
# 07. PAYOUT DATE CALCULATION

# =========================================
def calculate_payout_date(start_date, frequency, position):
    """
    Calculate each member's payout date
    according to the Jamiyah frequency.
    """
    if frequency == Jamiyah.Frequency.WEEKLY:
        return start_date + timedelta(
            weeks=position - 1
        )
    if frequency == Jamiyah.Frequency.MONTHLY:
        month_index = (
            start_date.year * 12
            + start_date.month - 1
            + position - 1
        )
        year, zero_based_month = divmod(
            month_index,
            12
        )
        month = zero_based_month + 1
        day = min(
            start_date.day,
            calendar.monthrange(year, month)[1]
        )
        return start_date.replace(
            year=year,
            month=month,
            day=day
        )
    raise ValueError(
        "دورية الجمعية غير مدعومة."
    )

# =========================================
# 08. GENERATE PAYOUT SCHEDULE

# =========================================
@login_required
@require_POST
def generate_payout_schedule(request, pk):
    with transaction.atomic():
        jamiyah = get_object_or_404(
            Jamiyah.objects.select_for_update(),
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
        if jamiyah.status != Jamiyah.Status.OPEN:
            messages.error(
                request,
                "لا يمكن تعديل جدول جمعية بدأت بالفعل."
            )
            return redirect("jamiyah_detail", pk=pk)
        if not jamiyah.start_date:
            messages.error(
                request,
                "يجب تحديد تاريخ بداية الجمعية أولًا."
            )
            return redirect("jamiyah_detail", pk=pk)
        approved_members = list(
            Membership.objects
            .filter(
                jamiyah=jamiyah,
                status=Membership.Status.APPROVED
            )
            .select_related("user")
        )
        if len(approved_members) != jamiyah.max_members:
            messages.error(
                request,
                "يجب اكتمال عدد الأعضاء قبل تحديد الأدوار."
            )
            return redirect("jamiyah_detail", pk=pk)
        if PayoutTurn.objects.filter(
            jamiyah=jamiyah
        ).exists():
            messages.error(
                request,
                "يوجد جدول استلام محفوظ لهذه الجمعية."
            )
            return redirect("jamiyah_detail", pk=pk)
        raw_ids = request.POST.getlist(
            "member_order"
        )
        if len(raw_ids) != len(approved_members):
            messages.error(
                request,
                "يجب اختيار عضو لكل دور."
            )
            return redirect("jamiyah_detail", pk=pk)
        try:
            ordered_ids = [
                int(value) for value in raw_ids
            ]
        except (TypeError, ValueError):
            messages.error(
                request,
                "ترتيب الأعضاء غير صالح."
            )
            return redirect("jamiyah_detail", pk=pk)
        approved_ids = {
            membership.id
            for membership in approved_members
        }
        if (
            len(set(ordered_ids)) != len(approved_members)
            or set(ordered_ids) != approved_ids
        ):
            messages.error(
                request,
                "يجب ترتيب جميع الأعضاء دون تكرار."
            )
            return redirect("jamiyah_detail", pk=pk)
        members_by_id = {
            membership.id: membership
            for membership in approved_members
        }
        turns = []
        for position, membership_id in enumerate(
            ordered_ids,
            start=1
        ):
            turn = PayoutTurn(
                jamiyah=jamiyah,
                membership=members_by_id[membership_id],
                position=position,
                payout_date=calculate_payout_date(
                    jamiyah.start_date,
                    jamiyah.frequency,
                    position
                )
            )
            turn.full_clean()
            turns.append(turn)
        PayoutTurn.objects.bulk_create(turns)
        jamiyah.status = Jamiyah.Status.ACTIVE
        jamiyah.save(
            update_fields=["status"]
        )
    messages.success(
        request,
        "تم حفظ جدول الاستلام وتفعيل الجمعية بنجاح."
    )
    return redirect(
        "jamiyah_detail",
        pk=pk
    )

# =========================================
# 09. PRIVATE JAMIYAH INVITATION

# =========================================
@login_required
def private_jamiyah_invite(request, token):
    jamiyah = get_object_or_404(
        Jamiyah,
        invite_token=token,
        visibility=Jamiyah.Visibility.PRIVATE
    )
    my_membership = Membership.objects.filter(
        jamiyah=jamiyah,
        user=request.user
    ).first()
    if my_membership and my_membership.status == Membership.Status.APPROVED:
        return redirect("jamiyah_detail", pk=jamiyah.pk)
    approved_count = Membership.objects.filter(
        jamiyah=jamiyah,
        status=Membership.Status.APPROVED
    ).count()
    remaining_seats = max(jamiyah.max_members - approved_count, 0)
    can_request_join = (
        jamiyah.status == Jamiyah.Status.OPEN
        and remaining_seats > 0
        and my_membership is None
    )
    if request.method == "POST":
        if my_membership:
            messages.warning(request, "لديك طلب مسجل سابقًا لهذه الجمعية.")
            return redirect("private_jamiyah_invite", token=token)
        if not can_request_join:
            messages.error(request, "الانضمام غير متاح لهذه الجمعية حاليًا.")
            return redirect("private_jamiyah_invite", token=token)
        with transaction.atomic():
            locked_jamiyah = get_object_or_404(
                Jamiyah.objects.select_for_update(),
                pk=jamiyah.pk,
                invite_token=token,
                visibility=Jamiyah.Visibility.PRIVATE,
                status=Jamiyah.Status.OPEN
            )
            current_count = Membership.objects.filter(
                jamiyah=locked_jamiyah,
                status=Membership.Status.APPROVED
            ).count()
            if current_count >= locked_jamiyah.max_members:
                messages.error(request, "اكتمل عدد أعضاء الجمعية.")
                return redirect("private_jamiyah_invite", token=token)
            Membership.objects.create(
                jamiyah=locked_jamiyah,
                user=request.user,
                role=Membership.Role.MEMBER,
                status=Membership.Status.PENDING
            )
        messages.success(
            request,
            "تم إرسال طلب الانضمام إلى مدير الجمعية بنجاح."
        )
        return redirect("private_jamiyah_invite", token=token)
    context = {
        "jamiyah": jamiyah,
        "my_membership": my_membership,
        "approved_count": approved_count,
        "remaining_seats": remaining_seats,
        "can_request_join": can_request_join,
    }
    return render(request, "jamiyahs/invite.html", context)

# =========================================
# 10. REGENERATE PRIVATE INVITE LINK

# =========================================
@login_required
@require_POST
def regenerate_invite_link(request, pk):
    jamiyah = get_object_or_404(
        Jamiyah,
        pk=pk,
        visibility=Jamiyah.Visibility.PRIVATE
    )
    is_manager = Membership.objects.filter(
        jamiyah=jamiyah,
        user=request.user,
        role=Membership.Role.MANAGER,
        status=Membership.Status.APPROVED
    ).exists()
    if not is_manager:
        raise Http404("غير مسموح.")
    jamiyah.invite_token = uuid.uuid4()
    jamiyah.save(update_fields=["invite_token"])
    messages.success(request, "تم إنشاء رابط دعوة جديد وإلغاء الرابط السابق.")
    return redirect("jamiyah_detail", pk=pk)

# =========================================
# 11. PAYOUT DELIVERY DASHBOARD

# =========================================
@login_required
def payout_delivery_dashboard(request, pk):
    jamiyah = get_object_or_404(Jamiyah, pk=pk)
    my_membership = Membership.objects.filter(
        jamiyah=jamiyah,
        user=request.user,
        status=Membership.Status.APPROVED
    ).first()
    if not my_membership:
        raise Http404("هذه الصفحة متاحة لأعضاء الجمعية فقط.")
    is_manager = my_membership.role == Membership.Role.MANAGER
    required_count = Membership.objects.filter(
        jamiyah=jamiyah,
        status=Membership.Status.APPROVED
    ).count()
    payout_amount = jamiyah.contribution_amount * jamiyah.max_members
    turns = PayoutTurn.objects.filter(
        jamiyah=jamiyah
    ).select_related(
        "membership__user",
        "delivered_by"
    ).order_by("position")
    delivery_rows = []
    for turn in turns:
        verified_count = Payment.objects.filter(
            jamiyah=jamiyah,
            payout_turn=turn,
            status=Payment.Status.VERIFIED
        ).count()
        ready_to_deliver = (
            jamiyah.status == Jamiyah.Status.ACTIVE
            and required_count == jamiyah.max_members
            and verified_count == required_count
            and turn.delivered_at is None
        )
        delivery_rows.append({
            "turn": turn,
            "verified_count": verified_count,
            "required_count": required_count,
            "payout_amount": payout_amount,
            "ready_to_deliver": ready_to_deliver,
            "is_recipient": turn.membership_id == my_membership.pk,
        })
    context = {
        "jamiyah": jamiyah,
        "is_manager": is_manager,
        "delivery_rows": delivery_rows,
    }
    return render(request, "jamiyahs/delivery.html", context)

# =========================================
# 12. CONFIRM PAYOUT DELIVERY - MANAGER

# =========================================
@login_required
@require_POST
def confirm_payout_delivery(request, pk, turn_id):
    with transaction.atomic():
        jamiyah = get_object_or_404(
            Jamiyah.objects.select_for_update(),
            pk=pk
        )
        is_manager = Membership.objects.filter(
            jamiyah=jamiyah,
            user=request.user,
            role=Membership.Role.MANAGER,
            status=Membership.Status.APPROVED
        ).exists()
        if not is_manager:
            raise Http404("تأكيد التسليم متاح لمدير الجمعية فقط.")
        turn = get_object_or_404(
            PayoutTurn.objects.select_for_update(),
            pk=turn_id,
            jamiyah=jamiyah
        )
        if turn.delivered_at:
            messages.info(
                request,
                "تم تأكيد تسليم هذه الدورة مسبقًا."
            )
            return redirect("jamiyah_detail", pk=pk)
        approved_count = Membership.objects.filter(
            jamiyah=jamiyah,
            status=Membership.Status.APPROVED
        ).count()
        verified_count = Payment.objects.filter(
            jamiyah=jamiyah,
            payout_turn=turn,
            status=Payment.Status.VERIFIED
        ).count()
        previous_undelivered_exists = PayoutTurn.objects.filter(
            jamiyah=jamiyah,
            position__lt=turn.position,
            delivered_at__isnull=True
        ).exists()
        if previous_undelivered_exists:
            messages.error(
                request,
                "يجب تأكيد تسليم جميع الأدوار السابقة أولًا."
            )
        elif jamiyah.status != Jamiyah.Status.ACTIVE:
            messages.error(
                request,
                "لا يمكن تأكيد التسليم إلا لجمعية جارية."
            )
        elif approved_count != jamiyah.max_members:
            messages.error(
                request,
                "يجب اكتمال عدد أعضاء الجمعية أولًا."
            )
        elif verified_count != approved_count:
            messages.error(
                request,
                "يجب توثيق جميع اشتراكات الدورة أولًا."
            )
        else:
            now = timezone.now()
            turn.delivered_at = now
            turn.delivered_by = request.user
            turn.recipient_seen_at = None
            turn.save(update_fields=[
                "delivered_at",
                "delivered_by",
                "recipient_seen_at"
            ])
            all_turns = PayoutTurn.objects.filter(
                jamiyah=jamiyah
            )
            total_turns = all_turns.count()
            delivered_turns = all_turns.filter(
                delivered_at__isnull=False
            ).count()
            if (
                total_turns == jamiyah.max_members
                and delivered_turns == total_turns
            ):
                jamiyah.status = Jamiyah.Status.COMPLETED
                jamiyah.completed_at = now
                jamiyah.save(update_fields=[
                    "status",
                    "completed_at"
                ])
                messages.success(
                    request,
                    "تم تأكيد تسليم آخر دورة واكتمال الجمعية بنجاح."
                )
            else:
                messages.success(
                    request,
                    "تم تسجيل تأكيد تسليم مبلغ الدورة، وسيظهر إشعار للمستلم."
                )
    return redirect("jamiyah_detail", pk=pk)

# =========================================
# 13. MARK DELIVERY NOTIFICATION AS READ

# =========================================
@login_required
@require_POST
def mark_payout_delivery_seen(request, pk, turn_id):
    turn = get_object_or_404(
        PayoutTurn,
        pk=turn_id,
        jamiyah_id=pk,
        membership__user=request.user,
        membership__status=Membership.Status.APPROVED,
        delivered_at__isnull=False
    )
    if turn.recipient_seen_at is None:
        turn.recipient_seen_at = timezone.now()
        turn.save(update_fields=["recipient_seen_at"])
    return redirect("jamiyah_detail", pk=pk)

# =========================================
# 14. MARK COMPLETION NOTIFICATION AS READ

# =========================================
@login_required
@require_POST
def mark_jamiyah_completion_seen(request, pk):
    membership = get_object_or_404(
        Membership,
        jamiyah_id=pk,
        user=request.user,
        status=Membership.Status.APPROVED,
        jamiyah__status=Jamiyah.Status.COMPLETED,
        jamiyah__completed_at__isnull=False
    )
    if membership.completion_seen_at is None:
        membership.completion_seen_at = timezone.now()
        membership.save(update_fields=["completion_seen_at"])
    return redirect("jamiyah_detail", pk=pk)
