"""Data migration: existing accounts switch from password login to email OTP / Google.

Every existing non-staff, non-superuser User gets set_unusable_password() so a
stale password hash can no longer be used to sign in (there is no more
password-based LoginView). Superusers/staff are deliberately excluded: they
still sign in with a real password at /admin/ (see `create_superuser`), and
this migration has no reverse (we don't keep the original password hashes) -
stripping their passwords would be an irreversible lockout.
"""

from django.contrib.auth.hashers import make_password
from django.db import migrations

UNUSABLE_PASSWORD_PREFIX = "!"


def set_unusable_passwords(apps, schema_editor):
    User = apps.get_model("authentication", "User")
    queryset = (
        User.objects.exclude(password__startswith=UNUSABLE_PASSWORD_PREFIX)
        .exclude(is_superuser=True)
        .exclude(is_staff=True)
    )
    for user in queryset.iterator():
        # make_password(None) already returns an unusable ("!"-prefixed) hash -
        # mirrors AbstractBaseUser.set_unusable_password(), unavailable on this
        # historical (data-migration) model.
        user.password = make_password(None)
        user.save(update_fields=["password"])


def noop_reverse(apps, schema_editor):
    """Not reversible: we don't keep the original password hashes."""


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0010_remove_user_failed_login_attempts_and_more"),
    ]

    operations = [
        migrations.RunPython(set_unusable_passwords, noop_reverse),
    ]
