from django.conf import settings
from rest_framework import permissions


class IsAdminToken(permissions.BasePermission):
    """Validate X-Admin-Token header against settings."""

    def has_permission(self, request, view):
        token = request.headers.get("X-Admin-Token") or request.META.get("HTTP_X_ADMIN_TOKEN")
        expected = getattr(settings, "LAZULI_ADMIN_TOKEN", "")
        return bool(token and expected and token.strip() == expected.strip())
