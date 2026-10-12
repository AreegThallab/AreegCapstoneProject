
from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = [
        "jamiyah",
        "membership",
        "payout_turn",
        "status",
        "reported_at",
        "reviewed_by",
        "reviewed_at",
    ]

    list_filter = [
        "status",
        "jamiyah",
        "reported_at",
    ]

    search_fields = [
        "jamiyah__name",
        "membership__user__username",
    ]

    readonly_fields = [
        "reported_at",
        "reviewed_at",
    ]
