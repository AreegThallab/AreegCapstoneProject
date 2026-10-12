
import uuid
from django.db import migrations


def populate_invite_tokens(apps, schema_editor):
    Jamiyah = apps.get_model("jamiyahs", "Jamiyah")
    for jamiyah in Jamiyah.objects.filter(invite_token__isnull=True):
        jamiyah.invite_token = uuid.uuid4()
        jamiyah.save(update_fields=["invite_token"])


class Migration(migrations.Migration):
    dependencies = [
        ("jamiyahs", "0003_jamiyah_invite_token"),
    ]

    operations = [
        migrations.RunPython(
            populate_invite_tokens,
            migrations.RunPython.noop
        ),
    ]
