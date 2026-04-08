from django.conf import settings


def oidc_enabled(request):
    return {
        'oidc_enabled': getattr(settings, 'OIDC_ENABLED', False)
    }
