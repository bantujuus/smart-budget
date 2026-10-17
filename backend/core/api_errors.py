"""
One error format for the whole API (docs/08_API_Specification.pdf, section 4):

    {"error": {"code": "VALIDATION_ERROR", "message": "...", "fields": {...}}}
"""
from rest_framework import exceptions
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    # Let DRF do its normal work first (it picks the HTTP status for us).
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