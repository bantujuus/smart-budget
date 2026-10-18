"""Role-based access control (RBAC).

Two roles:
  * user  - a normal account: can only ever see and change its OWN records.
  * admin - a staff account: can run the system (manage default categories, deactivate
            accounts, see system statistics) but has no special access to anyone's money:
            the finance endpoints are owner-scoped for everybody, admins included.

The role is stored in Django's existing `is_staff` flag, so it can only be changed by a
database administrator (python manage.py createsuperuser, or Django admin), never through
the public API. That blocks "mass assignment" attacks where someone registers with
{"is_staff": true}.
"""
from rest_framework.permissions import BasePermission


def role_of(user) -> str:
    return "admin" if (user.is_staff or user.is_superuser) else "user"


class IsAdminRole(BasePermission):
    """Allow only signed-in users whose role is admin (everyone else gets 403)."""

    message = "Administrator access is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and role_of(user) == "admin")