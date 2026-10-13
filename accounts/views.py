
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .forms import RegisterForm, ProfileForm
from .models import Profile

from jamiyahs.models import Jamiyah, Membership
from transactions.models import Payment


# =========================================
# 01. REGISTER VIEW
# =========================================
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            # Create User and Profile together
            with transaction.atomic():
                user = form.save(commit=False)
                user.email = form.cleaned_data["email"]
                user.save()

                Profile.objects.create(
                    user=user,
                    full_name=form.cleaned_data["full_name"],
                    phone_number=form.cleaned_data["phone_number"]
                )

            messages.success(
                request,
                "تم إنشاء حسابك بنجاح!"
            )
            return redirect("login")
    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form}
    )


# =========================================
# 02. PROFILE VIEW
# =========================================
@login_required
def profile_view(request):
    # Current logged-in user's profile
    profile = request.user.profile

    # =====================================
    # UPDATE PROFILE INFORMATION
    # =====================================
    if request.method == "POST":
        form = ProfileForm(
            request.POST,
            instance=profile
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "تم تحديث بياناتك بنجاح."
            )
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)

    # =====================================
    # GET APPROVED MEMBERSHIPS
    # =====================================
    approved_memberships = (
        Membership.objects
        .filter(
            user=request.user,
            status=Membership.Status.APPROVED
        )
        .select_related("jamiyah")
        .order_by("-joined_at")
    )

    # =====================================
    # CURRENT JAMIYAHS
    # OPEN + ACTIVE
    # =====================================
    current_memberships = approved_memberships.filter(
        jamiyah__status__in=[
            Jamiyah.Status.OPEN,
            Jamiyah.Status.ACTIVE
        ]
    )

    # =====================================
    # PREVIOUS JAMIYAHS
    # COMPLETED
    # =====================================
    previous_memberships = approved_memberships.filter(
        jamiyah__status=Jamiyah.Status.COMPLETED
    ).order_by(
        "-jamiyah__completed_at",
        "-joined_at"
    )

    # =====================================
    # CANCELLED JAMIYAHS
    # CANCELLED
    # =====================================
    cancelled_memberships = approved_memberships.filter(
        jamiyah__status=Jamiyah.Status.CANCELLED
    )

    # =====================================
    # PROFILE STATISTICS
    # =====================================
    total_jamiyahs = approved_memberships.count()

    managed_jamiyahs = approved_memberships.filter(
        role=Membership.Role.MANAGER
    ).count()

    joined_jamiyahs = approved_memberships.filter(
        role=Membership.Role.MEMBER
    ).count()

    verified_payments = Payment.objects.filter(
        membership__user=request.user,
        status=Payment.Status.VERIFIED
    ).count()

    # =====================================
    # SECTION COUNTS
    # =====================================
    current_jamiyahs_count = current_memberships.count()
    previous_jamiyahs_count = previous_memberships.count()
    cancelled_jamiyahs_count = cancelled_memberships.count()

    # =====================================
    # LISTS FOR PROFILE PAGE
    # =====================================
    recent_memberships = current_memberships[:3]
    cancelled_memberships = cancelled_memberships[:3]

    # =====================================
    # TEMPLATE CONTEXT
    # =====================================
    context = {
        "form": form,
        "profile": profile,
        "total_jamiyahs": total_jamiyahs,
        "managed_jamiyahs": managed_jamiyahs,
        "joined_jamiyahs": joined_jamiyahs,
        "verified_payments": verified_payments,

        "current_jamiyahs_count": current_jamiyahs_count,
        "previous_jamiyahs_count": previous_jamiyahs_count,
        "cancelled_jamiyahs_count": cancelled_jamiyahs_count,

        "recent_memberships": recent_memberships,
        "previous_memberships": previous_memberships,
        "cancelled_memberships": cancelled_memberships,
    }

    return render(
        request,
        "accounts/profile.html",
        context
    )
