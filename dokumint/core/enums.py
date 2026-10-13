from django.utils.translation import gettext_lazy as _

# Mapping of receipt review status to Boolean Values
DOCUMENT_REIVEW_STATUS_MAPPING = {
    'True': _('Reviewed'),
    'False': _('Pending Review')
}

# Mapping of notifications allowed status to Boolean Values
NOTIFICATIONS_ALLOWED_STATUS_MAPPING = {
    'True': _('Allowed'),
    'False': _('Not Allowed')
}

# Mapping of analytics allowed status to Boolean Values
ANALYTICS_ALLOWED_STATUS_MAPPING = {
    'True': _('Allowed'),
    'False': _('Not Allowed')
}