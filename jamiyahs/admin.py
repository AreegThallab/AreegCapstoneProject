
from django.contrib import admin

from .models import Jamiyah, Membership, PayoutTurn


# =========================================
# 01. JAMIYAH ADMIN
# =========================================

@admin.register(Jamiyah)
class JamiyahAdmin(admin.ModelAdmin):

    list_display = [
        "name",
        "creator",
        "contribution_amount",
        "max_members",
        "frequency",
        "start_date",
        "visibility",
        "status",
        "created_at",
    ]

    list_filter = [
        "frequency",
        "visibility",
        "status",
        "created_at",
    ]

    search_fields = [
        "name",
        "creator__username",
    ]


# =========================================
# 02. MEMBERSHIP ADMIN
# =========================================

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):

    list_display = [
        "user",
        "jamiyah",
        "role",
        "status",
        "joined_at",
    ]

    list_filter = [
        "role",
        "status",
    ]

    search_fields = [
        "user__username",
        "jamiyah__name",
    ]


# =========================================
# 03. PAYOUT TURN ADMIN
# =========================================

@admin.register(PayoutTurn)
class PayoutTurnAdmin(admin.ModelAdmin):

    list_display = [
        "jamiyah",
        "membership",
        "position",
        "payout_date",
    ]

    list_filter = [
        "jamiyah",
        "payout_date",
    ]

    search_fields = [
        "jamiyah__name",
        "membership__user__username",
    ]

    ordering = [
        "jamiyah",
        "position",
    ]
