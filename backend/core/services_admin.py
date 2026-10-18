"""Administrator operations (called only from views protected by IsAdminRole).

Every change is written to the audit log: who did what, to which record, and when.
Admins work with accounts and system settings; nothing here reads anyone's transactions,
budgets or goals, only counts.
"""
import logging
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.utils import timezone

from .models import Budget, Category, GoalContribution, SavingsGoal, Transaction, User
from .services import Conflict, NotFound, _field_error, _is_uuid

audit = logging.getLogger("smartbudget.audit")


# ----------------------------- default (system) categories ----------------------------- #
def create_system_category(admin, *, name, kind) -> Category:
    name = (name or "").strip()
    if not name:
        raise _field_error("name", "Name is required.")
    if kind not in ("income", "expense", "both"):
        raise _field_error("kind", "Kind must be income, expense or both.")
    try:
        with transaction.atomic():
            category = Category.objects.create(user=None, name=name, kind=kind)
    except IntegrityError:
        raise Conflict("A default category with this name and kind already exists.", {"name": ["Already exists."]})
    audit.info("admin=%s action=create_default_category category=%s name=%r", admin.id, category.id, name)
    return category


def archive_system_category(admin, category_id) -> Category:
    """Hide a default category from new records. Old transactions keep it (history is never lost)."""
    if not _is_uuid(category_id):
        raise NotFound("Category not found.")
    with transaction.atomic():
        try:
            category = Category.objects.select_for_update().get(id=category_id, user__isnull=True)
        except Category.DoesNotExist:
            raise NotFound("Default category not found.")
        category.is_archived = True
        category.save(update_fields=["is_archived"])
    audit.info("admin=%s action=archive_default_category category=%s", admin.id, category.id)
    return category


# ----------------------------- accounts ----------------------------- #
def set_user_active(admin, user_id, is_active: bool) -> User:
    """Deactivate (or reactivate) an account. A deactivated user cannot log in and any
    session they already have stops working. Nothing is deleted."""
    if not _is_uuid(user_id):
        raise NotFound("User not found.")
    if str(admin.id) == str(user_id) and not is_active:
        raise _field_error("is_active", "You cannot deactivate your own account.")
    with transaction.atomic():
        try:
            user = User.objects.select_for_update().get(id=user_id)
        except User.DoesNotExist:
            raise NotFound("User not found.")
        user.is_active = is_active
        user.save(update_fields=["is_active"])
    audit.info("admin=%s action=set_user_active target=%s is_active=%s", admin.id, user.id, is_active)
    return user


# ----------------------------- statistics ----------------------------- #
def system_stats() -> dict:
    """Counts only - never amounts, balances or anyone's individual records."""
    now = timezone.now()
    users = User.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        admins=Count("id", filter=Q(is_staff=True) | Q(is_superuser=True)),
        new_last_30_days=Count("id", filter=Q(created_at__gte=now - timedelta(days=30))),
    )
    by_status = dict(SavingsGoal.objects.values_list("status").annotate(n=Count("id")))
    return {
        "users": users,
        "records": {
            "transactions": Transaction.objects.count(),
            "budgets": Budget.objects.count(),
            "goal_contributions": GoalContribution.objects.count(),
        },
        "goals_by_status": {s: by_status.get(s, 0) for s in ("active", "paused", "completed", "archived")},
        "categories": {
            "default": Category.objects.filter(user__isnull=True, is_archived=False).count(),
            "custom": Category.objects.filter(user__isnull=False, is_archived=False).count(),
        },
        "generated_at": now,
    }