"""Extra budget write operations (edit and delete).

core/services.py already has create_budget. The API spec also asks for PATCH and DELETE
on budgets, so they live here, written in the same style: owner-scoped, atomic, and the
database's no-overlap rule is translated into a friendly Conflict error.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction

from .models import Budget
from .services import (
    Conflict,
    NotFound,
    ValidationFailed,
    _clean,
    _date,
    _field_error,
    _is_uuid,
    _money,
)


def update_budget(user, budget_id, /, **changes) -> Budget:
    """Change period_type / start_date / end_date / limit_amount of the user's own budget.
    (The category cannot be changed: create a new budget instead.)"""
    allowed = {"period_type", "start_date", "end_date", "limit_amount"}
    unknown = set(changes) - allowed
    if unknown:
        raise ValidationFailed("Unknown field.", {f: ["This field cannot be changed."] for f in unknown})

    with transaction.atomic():
        try:
            budget = (
                Budget.objects.select_for_update(of=("self",))
                .select_related("category")
                .get(id=budget_id, user=user)
            )
        except (Budget.DoesNotExist, ValueError, DjangoValidationError):
            raise NotFound("Budget not found.")

        if "period_type" in changes:
            if changes["period_type"] not in ("weekly", "monthly", "custom"):
                raise _field_error("period_type", "Choose weekly, monthly or custom.")
            budget.period_type = changes["period_type"]
        if "start_date" in changes:
            budget.start_date = _date(changes["start_date"], "start_date")
        if "end_date" in changes:
            budget.end_date = _date(changes["end_date"], "end_date")
        if "limit_amount" in changes:
            budget.limit_amount = _money(changes["limit_amount"], "limit_amount")
        if budget.end_date < budget.start_date:
            raise _field_error("end_date", "End date must not be before the start date.")

        _clean(budget)
        try:
            with transaction.atomic():  # savepoint, so a refused UPDATE leaves the outer block usable
                budget.save()
        except IntegrityError:
            raise Conflict(
                "A budget for this category already covers part of that period.",
                {"start_date": ["Overlaps an existing budget for this category."]},
            )
        return budget


def delete_budget(user, budget_id) -> None:
    if not _is_uuid(budget_id):
        raise NotFound("Budget not found.")
    deleted, _ = Budget.objects.filter(id=budget_id, user=user).delete()
    if not deleted:
        raise NotFound("Budget not found.")