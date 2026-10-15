"""
Write operations ("services") for the Smart Budgeting and Financial Goal Management System.

core/queries.py reads data; this module changes it. API views should call these
functions rather than touching the models directly.

Transaction rules used throughout
---------------------------------
* ATOMIC     A write that changes more than one row runs inside `transaction.atomic()`.
             If anything fails, PostgreSQL rolls back every change in the block.
* LOCKING    Before changing a row that other requests may change at the same time
             (a goal's total and status), we lock it with `select_for_update()`.
             A second request for the same row waits until the first one commits, then
             sees the committed result. This prevents lost updates and double
             completion. Only ONE row is locked per operation, so two requests can
             never wait on each other in a circle (no deadlocks).
* OWNERSHIP  The first argument is always the authenticated `user`. Rows are looked up
             with `user=user`, so another user's id behaves exactly like a missing id
             (NotFound); we never reveal that it exists.
* MONEY      Amounts are `Decimal` with at most 2 decimal places. `float` is rejected.

Errors
------
Every failure raises a `ServiceError` with a machine-readable `code`, a message and
(optionally) per-field messages, matching the error format in docs/08_API_Specification:
    {"error": {"code": "VALIDATION_ERROR", "message": "...", "fields": {"amount": ["..."]}}}
"""
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce

from .models import Budget, Category, GoalContribution, SavingsGoal, Transaction

MAX_MONEY = Decimal("9999999999.99")        # largest value DECIMAL(12,2) can hold


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #
class ServiceError(Exception):
    """Base class. `http_status` is a suggestion for the API layer."""
    code = "ERROR"
    http_status = 400

    def __init__(self, message, fields=None):
        super().__init__(message)
        self.message = message
        self.fields = fields or {}

    def as_dict(self):
        return {"error": {"code": self.code, "message": self.message, "fields": self.fields}}


class ValidationFailed(ServiceError):
    code, http_status = "VALIDATION_ERROR", 400


class NotFound(ServiceError):
    code, http_status = "NOT_FOUND", 404


class Conflict(ServiceError):
    """The request is valid but clashes with the current state (overlapping budget,
    goal not active, illegal status change ...)."""
    code, http_status = "CONFLICT", 409


def _field_error(field, message):
    return ValidationFailed("Please correct the highlighted fields.", {field: [message]})


# --------------------------------------------------------------------------- #
# Validation helpers
# --------------------------------------------------------------------------- #
def _money(value, field="amount") -> Decimal:
    """Accept Decimal / int / numeric string. Reject float, <= 0, > 2 decimals, too large."""
    if isinstance(value, bool) or isinstance(value, float):
        raise _field_error(field, "Send money as a string or whole number, not a floating-point number.")
    try:
        d = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise _field_error(field, "Enter a valid amount.")
    if not d.is_finite():
        raise _field_error(field, "Enter a valid amount.")
    if d <= 0:
        raise _field_error(field, "Amount must be greater than zero.")
    if d != d.quantize(Decimal("0.01")):
        raise _field_error(field, "Amount can have at most 2 decimal places.")
    if d > MAX_MONEY:
        raise _field_error(field, "Amount is too large.")
    return d.quantize(Decimal("0.01"))


def _date(value, field) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise _field_error(field, "Enter a valid date (YYYY-MM-DD).")


def _clean(instance):
    """Run the model's own validation (`clean()`), turning Django errors into ours."""
    try:
        instance.clean()
    except DjangoValidationError as e:
        raise ValidationFailed("Please correct the highlighted fields.", e.message_dict)


def _is_uuid(value) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


def _usable_category(user, category_id) -> Category:
    """A category the user may use: their own or a system default, and not archived."""
    try:
        return Category.objects.get(
            Q(user=user) | Q(user__isnull=True), id=category_id, is_archived=False
        )
    except (Category.DoesNotExist, ValueError, DjangoValidationError):
        raise NotFound("Category not found.", {"category_id": ["Choose a valid category."]})


def _owned_goal(user, goal_id, *, lock=False) -> SavingsGoal:
    qs = SavingsGoal.objects.filter(user=user)
    if lock:
        qs = qs.select_for_update()
    try:
        return qs.get(id=goal_id)
    except (SavingsGoal.DoesNotExist, ValueError, DjangoValidationError):
        raise NotFound("Savings goal not found.")


def _contributed_total(goal) -> Decimal:
    return GoalContribution.objects.filter(goal=goal).aggregate(
        t=Coalesce(Sum("amount"), Decimal("0.00"))
    )["t"]


# --------------------------------------------------------------------------- #
# Transactions (income / expense records)
# --------------------------------------------------------------------------- #
def create_transaction(user, *, category_id, type, amount, transaction_date, note=None) -> Transaction:
    if type not in ("income", "expense"):
        raise _field_error("type", "Type must be 'income' or 'expense'.")
    tx = Transaction(
        user=user,                                    # owner comes from the session, never the request
        category=_usable_category(user, category_id),
        type=type,
        amount=_money(amount),
        transaction_date=_date(transaction_date, "transaction_date"),
        note=(note or None),
    )
    _clean(tx)                                        # category kind must match the type
    tx.save()
    return tx


def update_transaction(user, transaction_id, /, **changes) -> Transaction:
    """Change category / type / amount / transaction_date / note. The row is locked
    so two simultaneous edits cannot overwrite each other half-way."""
    allowed = {"category_id", "type", "amount", "transaction_date", "note"}
    unknown = set(changes) - allowed
    if unknown:
        raise ValidationFailed("Unknown field.", {f: ["This field cannot be changed."] for f in unknown})
    with transaction.atomic():
        try:
            tx = Transaction.objects.select_for_update().get(id=transaction_id, user=user)
        except (Transaction.DoesNotExist, ValueError, DjangoValidationError):
            raise NotFound("Transaction not found.")
        if "type" in changes:
            if changes["type"] not in ("income", "expense"):
                raise _field_error("type", "Type must be 'income' or 'expense'.")
            tx.type = changes["type"]
        if "category_id" in changes:
            tx.category = _usable_category(user, changes["category_id"])
        if "amount" in changes:
            tx.amount = _money(changes["amount"])
        if "transaction_date" in changes:
            tx.transaction_date = _date(changes["transaction_date"], "transaction_date")
        if "note" in changes:
            tx.note = changes["note"] or None
        _clean(tx)                                    # re-check category vs type after ANY change
        tx.save()
        return tx


def delete_transaction(user, transaction_id) -> None:
    if not _is_uuid(transaction_id):
        raise NotFound("Transaction not found.")
    deleted, _ = Transaction.objects.filter(id=transaction_id, user=user).delete()
    if not deleted:
        raise NotFound("Transaction not found.")


# --------------------------------------------------------------------------- #
# Categories
# --------------------------------------------------------------------------- #
def create_category(user, *, name, kind) -> Category:
    name = (name or "").strip()
    if not name:
        raise _field_error("name", "Name is required.")
    if kind not in ("income", "expense", "both"):
        raise _field_error("kind", "Kind must be income, expense or both.")
    try:
        with transaction.atomic():                    # savepoint: a failed INSERT must not poison an outer transaction
            return Category.objects.create(user=user, name=name, kind=kind)
    except IntegrityError:
        raise Conflict("You already have a category with this name and kind.", {"name": ["Already exists."]})


def archive_category(user, category_id) -> Category:
    """Hide a category from new records. Old transactions and budgets keep pointing
    at it (their foreign key is PROTECTed), so history is never lost. System default
    categories belong to nobody and cannot be archived by a user."""
    with transaction.atomic():
        try:
            cat = Category.objects.select_for_update().get(id=category_id, user=user)
        except (Category.DoesNotExist, ValueError, DjangoValidationError):
            raise NotFound("Category not found.")
        cat.is_archived = True
        cat.save(update_fields=["is_archived"])
        return cat


# --------------------------------------------------------------------------- #
# Budgets
# --------------------------------------------------------------------------- #
def create_budget(user, *, category_id, period_type, start_date, end_date, limit_amount) -> Budget:
    if period_type not in ("weekly", "monthly", "custom"):
        raise _field_error("period_type", "Choose weekly, monthly or custom.")
    start, end = _date(start_date, "start_date"), _date(end_date, "end_date")
    if end < start:
        raise _field_error("end_date", "End date must not be before the start date.")
    budget = Budget(
        user=user, category=_usable_category(user, category_id), period_type=period_type,
        start_date=start, end_date=end, limit_amount=_money(limit_amount, "limit_amount"),
    )
    _clean(budget)
    try:
        with transaction.atomic():
            budget.save()
    except IntegrityError:
        # The database itself refuses overlapping periods (exclusion constraint
        # budget_no_overlap), so this is safe even if two requests arrive at once.
        raise Conflict(
            "A budget for this category already covers part of that period.",
            {"start_date": ["Overlaps an existing budget for this category."]},
        )
    return budget


# --------------------------------------------------------------------------- #
# Savings goals and contributions
# --------------------------------------------------------------------------- #
# Allowed status changes (status -> set of next statuses)
GOAL_TRANSITIONS = {
    "active": {"paused", "completed", "archived"},
    "paused": {"active", "archived"},
    "completed": {"active", "archived"},      # reopen allowed
    "archived": {"active"},                   # restore allowed
}


def create_goal(user, *, name, target_amount, target_date=None, initial_contribution=None) -> SavingsGoal:
    """Create a goal and, optionally, its first contribution as ONE atomic step:
    either both exist afterwards or neither does."""
    name = (name or "").strip()
    if not name:
        raise _field_error("name", "Name is required.")
    target = _money(target_amount, "target_amount")
    tdate = _date(target_date, "target_date") if target_date else None
    with transaction.atomic():
        goal = SavingsGoal.objects.create(user=user, name=name, target_amount=target, target_date=tdate)
        if initial_contribution is not None:
            record_contribution(user, goal.id, amount=initial_contribution, contribution_date=date.today())
            goal.refresh_from_db()
        return goal


def record_contribution(user, goal_id, *, amount, contribution_date, note=None):
    """Add money to a goal. Returns (contribution, goal, contributed_total).

    One atomic block:
      1. lock the goal row            (concurrent contributions queue up here)
      2. check the goal is active
      3. insert the contribution
      4. re-total the contributions   (sees every earlier committed one)
      5. mark the goal completed when the total reaches the target
    If step 3, 4 or 5 fails, nothing is saved.
    """
    amt = _money(amount)
    cdate = _date(contribution_date, "contribution_date")
    with transaction.atomic():
        goal = _owned_goal(user, goal_id, lock=True)
        if goal.status != "active":
            raise Conflict(f"This goal is {goal.status}. Make it active before adding money.")
        contribution = GoalContribution.objects.create(
            goal=goal, user=user, amount=amt, contribution_date=cdate, note=(note or None)
        )
        total = _contributed_total(goal)
        if total >= goal.target_amount:
            goal.status = "completed"
            goal.save(update_fields=["status"])
        return contribution, goal, total


def delete_contribution(user, goal_id, contribution_id):
    """Remove a contribution. A completed goal drops back to active if it is no
    longer fully funded. Returns (goal, contributed_total)."""
    with transaction.atomic():
        goal = _owned_goal(user, goal_id, lock=True)
        if not _is_uuid(contribution_id):
            raise NotFound("Contribution not found.")
        deleted, _ = GoalContribution.objects.filter(id=contribution_id, goal=goal, user=user).delete()
        if not deleted:
            raise NotFound("Contribution not found.")
        total = _contributed_total(goal)
        if goal.status == "completed" and total < goal.target_amount:
            goal.status = "active"
            goal.save(update_fields=["status"])
        return goal, total


def change_goal_status(user, goal_id, new_status) -> SavingsGoal:
    """Move a goal between statuses following GOAL_TRANSITIONS. Completing by hand is
    allowed. Re-opening a goal that is already fully funded is refused, because it
    would be marked completed again by the next contribution."""
    if new_status not in GOAL_TRANSITIONS:
        raise _field_error("status", "Status must be active, paused, completed or archived.")
    with transaction.atomic():
        goal = _owned_goal(user, goal_id, lock=True)
        if new_status == goal.status:
            return goal
        if new_status not in GOAL_TRANSITIONS[goal.status]:
            raise Conflict(f"A {goal.status} goal cannot become {new_status}.")
        if new_status == "active" and goal.status == "completed" \
                and _contributed_total(goal) >= goal.target_amount:
            raise Conflict("This goal is already fully funded. Raise the target to reopen it.")
        goal.status = new_status
        goal.save(update_fields=["status"])
        return goal
