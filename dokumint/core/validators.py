from django.core import validators
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class EmailRelayUsernameValidator(validators.RegexValidator):
    regex = r"^[a-zA-Z0-9_.]+$"
    message = _(
        "Invalid email relay username. This value may contain only unaccented lowercase a-z "
        "and uppercase A-Z letters, numbers, '.' and '_' characters."
    )
    flags = 0

