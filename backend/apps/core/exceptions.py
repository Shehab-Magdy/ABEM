"""Global DRF exception handler with i18n language activation."""
from django.conf import settings
from django.utils import translation
from rest_framework.views import exception_handler


def _activate_request_language(context):
    """Activate the language from Accept-Language header for this request."""
    request = context.get("request")
    if not request:
        return
    lang = getattr(request, "LANGUAGE_CODE", None)
    if not lang:
        accept = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
        lang = accept.split(",")[0].split(";")[0].strip()[:2].lower()
    supported = {code for code, _ in settings.LANGUAGES}
    if lang not in supported:
        lang = settings.LANGUAGE_CODE
    translation.activate(lang)


def custom_exception_handler(exc, context):
    _activate_request_language(context)
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            "status": "error",
            "code": response.status_code,
            "errors": response.data,
        }
    return response
