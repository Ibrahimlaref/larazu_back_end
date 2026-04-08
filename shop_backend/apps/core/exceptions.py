"""Custom exception handler for consistent error format: { "error": "message" }."""

import logging

from django.conf import settings
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def lazuli_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None and hasattr(response, "data"):
        data = response.data
        if isinstance(data, dict) and "error" not in data:
            if "detail" in data:
                response.data = {"error": str(data["detail"])}
            else:
                first_key = next(iter(data.keys()), None)
                if first_key:
                    vals = data[first_key]
                    msg = vals[0] if isinstance(vals, list) else str(vals)
                    response.data = {"error": msg}
    else:
        logger.exception("Unhandled API exception: %s", exc)
        from rest_framework.response import Response
        from rest_framework import status
        msg = "Internal server error"
        if getattr(settings, "DEBUG", False):
            msg = str(exc)
        response = Response({"error": msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return response
