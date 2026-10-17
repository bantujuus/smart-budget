"""
One error format for the whole API (docs/08_API_Specification.pdf, section 4):

    {"error": {"code": "VALIDATION_ERROR", "message": "...", "fields": {...}}}
"""
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .services import ServiceError


def api_exception_handler(exc, context):
    # Errors raised by services.py (not found, conflict, rule broken) already know their
    # own code, message and HTTP status, so we just wrap them.
    if isinstance(exc, ServiceError):
        return Response(exc.as_dict(), status=exc.http_status)

    # Everything else: let DRF do its normal work first (it picks the HTTP status for us).
    response = exception_handler(exc, context)
    if response is None:
        return None  # not an API error; Django handles it (500 etc.)

    if isinstance(exc, exceptions.ValidationError):
        fields = response.data if isinstance(response.data, dict) else {"non_field_errors": response.data}
        body = {
            "code": "VALIDATION_ERROR",
            "message": "Please correct the highlighted fields.",
            "fields": fields,
        }
    else:
        code = exc.get_codes() if hasattr(exc, "get_codes") else "error"
        body = {
            "code": str(code).upper(),
            "message": str(getattr(exc, "detail", "Request failed.")),
        }

    response.data = {"error": body}
    return response