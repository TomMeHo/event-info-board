import os
from django.conf import settings


def oidc_enabled(request):
    return {
        'oidc_enabled': getattr(settings, 'OIDC_ENABLED', False)
    }


def footer_settings(request):
    return {
        'FOOTER_LINK_URL': os.getenv('FOOTER_LINK_URL', 'https://dm2026.tv-hochstetten.de'),
        'FOOTER_LINK_LABEL': os.getenv('FOOTER_LINK_LABEL', 'Deutsche Meisterschaften 2026'),
        'FOOTER_IMPRESSUM_URL': os.getenv('FOOTER_IMPRESSUM_URL', 'https://www.tv-hochstetten.de/impressum')
    }
