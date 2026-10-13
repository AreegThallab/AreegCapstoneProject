
from django import forms
from django.utils import timezone

from .models import Jamiyah, Membership


# =========================================
# 01. CREATE JAMIYAH FORM
# =========================================

class JamiyahForm(forms.ModelForm):

    # Required for newly created Jamiyahs
    start_date = forms.DateField(
        required=True,
        label="تاريخ بداية الجمعية",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "type": "date"
            }
        )
    )

    class Meta:
        model = Jamiyah

        fields = [
            "name",
            "description",
            "contribution_amount",
            "max_members",
            "frequency",
            "start_date",
            "visibility",
        ]

        labels = {
            "name": "اسم الجمعية",
            "description": "وصف الجمعية",
            "contribution_amount": "مبلغ الاشتراك",
            "max_members": "عدد الأعضاء",
            "frequency": "دورية الجمعية",
            "start_date": "تاريخ بداية الجمعية",
            "visibility": "نوع الجمعية",
        }

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "مثال: جمعية الأصدقاء"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "placeholder": "اكتب وصفًا مختصرًا للجمعية...",
                    "rows": 4
                }
            ),

            "contribution_amount": forms.NumberInput(
                attrs={
                    "placeholder": "500",
                    "min": "1",
                    "step": "0.01"
                }
            ),

            "max_members": forms.NumberInput(
                attrs={
                    "placeholder": "6",
                    "min": "2",
                    "step": "1"
                }
            ),

            "frequency": forms.Select(),

            "visibility": forms.Select(),
        }

    # Validate Jamiyah name
    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        if not name:
            raise forms.ValidationError(
                "يرجى إدخال اسم الجمعية."
            )

        return name

    # Validate start date
    def clean_start_date(self):
        start_date = self.cleaned_data["start_date"]

        if start_date < timezone.localdate():
            raise forms.ValidationError(
                "تاريخ البداية لا يمكن أن يكون في الماضي."
            )

        return start_date


# =========================================
# 02. EDIT JAMIYAH FORM
# =========================================

class JamiyahEditForm(JamiyahForm):
    """
    Allows managers to update safe Jamiyah fields while preserving
    workflow records and existing memberships.
    """

    def clean_start_date(self):
        start_date = self.cleaned_data["start_date"]
        current_start_date = self.instance.start_date if self.instance else None

        if (
            start_date < timezone.localdate()
            and start_date != current_start_date
        ):
            raise forms.ValidationError(
                "تاريخ البداية لا يمكن أن يكون في الماضي."
            )

        return start_date

    def clean_max_members(self):
        max_members = self.cleaned_data["max_members"]

        if self.instance and self.instance.pk:
            committed_memberships = Membership.objects.filter(
                jamiyah=self.instance
            ).exclude(
                status=Membership.Status.REJECTED
            ).count()

            if max_members < committed_memberships:
                raise forms.ValidationError(
                    "عدد الأعضاء لا يمكن أن يكون أقل من الأعضاء المقبولين أو الطلبات المعلّقة."
                )

        return max_members

    def clean(self):
        cleaned_data = super().clean()

        if self.instance and self.instance.pk:
            if self.instance.status != Jamiyah.Status.OPEN:
                raise forms.ValidationError(
                    "لا يمكن تعديل جمعية بدأت أو اكتملت أو أُلغيت."
                )

            if self.instance.payout_turns.exists():
                raise forms.ValidationError(
                    "لا يمكن تعديل جمعية لديها جدول استلام محفوظ."
                )

        return cleaned_data
