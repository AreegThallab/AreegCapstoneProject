from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


# Saudi phone number validation
saudi_phone_validator = RegexValidator(
    regex=r"^\+9665\d{8}$",
    message="أدخل رقم جوال سعودي صحيح بصيغة +9665XXXXXXXX."
)


class Profile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    full_name = models.CharField(
        max_length=150
    )

    phone_number = models.CharField(
        max_length=13,
        unique=True,
        validators=[saudi_phone_validator]
    )

    def __str__(self):
        return self.full_name
