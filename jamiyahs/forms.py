
from django import forms
from django.utils import timezone

from .models import Jamiyah


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
