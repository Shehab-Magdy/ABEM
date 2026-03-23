"""Password complexity validator – enforced at API layer and Django auth level."""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class PasswordComplexityValidator:
    """
    Django AUTH_PASSWORD_VALIDATORS-compatible validator.
    Rules: min 8 chars, 1 uppercase, 1 digit, 1 special character.
    """

    def validate(self, password, user=None):
        errors = []
        if len(password) < 8:
            errors.append(_("Password must be at least 8 characters."))
        if not re.search(r"[A-Z]", password):
            errors.append(_("Password must contain at least one uppercase letter."))
        if not re.search(r"\d", password):
            errors.append(_("Password must contain at least one digit."))
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", password):
            errors.append(_("Password must contain at least one special character."))
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Password must be at least 8 characters and include "
            "an uppercase letter, a digit, and a special character."
        )


def validate_password_complexity(value):
    """Standalone callable for use in DRF serializer field validators."""
    PasswordComplexityValidator().validate(value)
