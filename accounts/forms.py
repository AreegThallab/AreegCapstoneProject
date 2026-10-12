
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Profile, saudi_phone_validator


# =========================================
# REGISTRATION FORM
# =========================================

class RegisterForm(UserCreationForm):

    full_name = forms.CharField(
        max_length=150,
        required=True,
        label="الاسم الكامل"
    )

    email = forms.EmailField(
        required=True,
        label="البريد الإلكتروني"
    )

    phone_number = forms.CharField(
        max_length=13,
        required=True,
        label="رقم الجوال",
        validators=[saudi_phone_validator]
    )

    class Meta:
        model = User
        fields = [
            "username",
            "full_name",
            "email",
            "phone_number",
            "password1",
            "password2",
        ]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "هذا البريد الإلكتروني مسجل مسبقًا."
            )

        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"]

        if Profile.objects.filter(
            phone_number=phone_number
        ).exists():
            raise forms.ValidationError(
                "رقم الجوال هذا مسجل مسبقًا."
            )

        return phone_number


# =========================================
# PROFILE UPDATE FORM
# =========================================

class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile

        fields = [
            "full_name",
            "phone_number",
        ]

        labels = {
            "full_name": "الاسم الكامل",
            "phone_number": "رقم الجوال",
        }

        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "placeholder": "الاسم الكامل"
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "placeholder": "+9665XXXXXXXX",
                    "dir": "ltr",
                    "inputmode": "tel"
                }
            ),
        }
