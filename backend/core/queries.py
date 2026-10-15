"""
Read-only ORM queries for the Smart Budgeting and Financial Goal Management System.

These implement the "calculation contract" in docs/08_API_Specification.pdf:

    income_total     sum of income transactions in the inclusive date range
    expense_total    sum of expense transactions in the inclusive date range
    net_cash_flow    income_total - expense_total   (NOT a verified bank balance)
    budget_used      sum of expenses matching the budget's category and period
    budget_remaining limit_amount - budget_used     (negative = overspent)
    goal_contributed sum of contributions linked to the goal
    goal_progress    goal_contributed / target_amount * 100 (bar capped at 100,
                     the real total is always returned separately)

Rules every function follows
----------------------------
* The first argument is ALWAYS the authenticated `user`. Every query filters on it,
  so one user can never read another user's records (FR-14). Never pass a user id
  taken from the request body.
* Date ranges are inclusive on both ends (start <= date <= end).
* Money stays `Decimal` end to end; nothing is converted to float.
* Totals are computed in the database (one aggregate query), not by looping in
  Python, and related rows are joined, so there are no N+1 query problems.
"""
from datetime import date
from decimal import Decimal

from django.db.models import (
    DecimalField, ExpressionWrapper, F, OuterRef, Q, QuerySet, Subquery, Sum, Value,
)
from django.db.models.functions import Coalesce, Greatest, Least, Round, TruncDay, TruncMonth, TruncWeek

from .models import Budget, GoalContribution, SavingsGoal, Transaction

ZERO = Value(Decimal("0.00"), output_field=DecimalField(max_digits=12, decimal_places=2))
MONEY_FIELD = DecimalField(max_digits=14, decimal_places=2)


def _check_range(start: date, end: date) -> None:
    if start > end:
        raise ValueError("start date must not be after end date")


def _owned_in_range(user, start: date, end: date) -> QuerySet:
    """The user's transactions with start <= transaction_date <= end."""
    return Transaction.objects.filter(
        user=user, transaction_date__gte=start, transaction_date__lte=end
    )


# --------------------------------------------------------------------------- #
# Transactions list (GET /transactions with filters)
# --------------------------------------------------------------------------- #
def list_transactions(user, *, type=None, category_id=None, start=None, end=None) -> QuerySet:
    """Filtered, newest-first transaction list. `select_related` fetches each
    category in the same SQL JOIN, so listing N rows costs 1 query, not N + 1."""
    qs = Transaction.objects.filter(user=user).select_related("category")
    if type:
        qs = qs.filter(type=type)
    if category_id:
        qs = qs.filter(category_id=category_id)
    if start:
        qs = qs.filter(transaction_date__gte=start)
    if end:
        qs = qs.filter(transaction_date__lte=end)
    return qs.order_by("-transaction_date", "-created_at")


# --------------------------------------------------------------------------- #
# Dashboard totals (GET /dashboard)
# --------------------------------------------------------------------------- #
def dashboard_totals(user, start: date, end: date) -> dict:
    """income_total, expense_total and net_cash_flow in ONE query.

    Conditional aggregation:  SUM(amount) FILTER (WHERE type = 'income') ...
    """
    _check_range(start, end)
    agg = _owned_in_range(user, start, end).aggregate(
        income_total=Coalesce(Sum("amount", filter=Q(type="income")), ZERO),
        expense_total=Coalesce(Sum("amount", filter=Q(type="expense")), ZERO),
    )
    agg["net_cash_flow"] = agg["income_total"] - agg["expense_total"]
    return agg


# --------------------------------------------------------------------------- #
# Reports: by category and over time (GET /reports/summary)
# --------------------------------------------------------------------------- #
def totals_by_category(user, start: date, end: date, type: str = "expense") -> list[dict]:
    """Spending (or income) per category, largest first, with each category's
    percentage share of the total. For the pie / bar chart."""
    _check_range(start, end)
    rows = list(
        _owned_in_range(user, start, end)
        .filter(type=type)
        .values("category_id", "category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total", "category__name")
    )
    grand = sum((r["total"] for r in rows), Decimal("0.00"))
    for r in rows:
        r["share_pct"] = (r["total"] / grand * 100).quantize(Decimal("0.1")) if grand else Decimal("0.0")
    return rows


_TRUNC = {"day": TruncDay, "week": TruncWeek, "month": TruncMonth}


def cash_flow_trend(user, start: date, end: date, granularity: str = "month") -> list[dict]:
    """Income, expenses and net per day / week / month, oldest first. For the
    line chart. Periods with no transactions are simply absent; the frontend
    should treat a missing period as zero."""
    _check_range(start, end)
    if granularity not in _TRUNC:
        raise ValueError("granularity must be 'day', 'week' or 'month'")
    rows = list(
        _owned_in_range(user, start, end)
        .annotate(period=_TRUNC[granularity]("transaction_date"))
        .values("period")
        .annotate(
            income=Coalesce(Sum("amount", filter=Q(type="income")), ZERO),
            expense=Coalesce(Sum("amount", filter=Q(type="expense")), ZERO),
        )
        .order_by("period")
    )
    for r in rows:
        r["net"] = r["income"] - r["expense"]
    return rows


# --------------------------------------------------------------------------- #
# Budgets (GET /budgets, dashboard budget panel)
# --------------------------------------------------------------------------- #
def budgets_with_usage(user, *, on_or_overlapping: tuple[date, date] | None = None) -> list[Budget]:
    """The user's budgets, each with `used`, `remaining`, `used_pct` and `is_over`.

    `used` is a correlated subquery: the sum of the user's expenses in the
    budget's category between the budget's own start and end dates. It is
    computed once per budget inside SQL, in a single round trip, and the other
    figures are derived from it in Python so the subquery is not repeated.
    A list is returned (a user has few budgets), with the extra attributes set
    on each Budget instance.
    """
    spent = (
        Transaction.objects.filter(
            user=OuterRef("user"),
            category=OuterRef("category"),
            type="expense",
            transaction_date__gte=OuterRef("start_date"),
            transaction_date__lte=OuterRef("end_date"),
        )
        .order_by()
        .values("user")                      # group everything into one row
        .annotate(total=Sum("amount"))
        .values("total")
    )
    qs = (
        Budget.objects.filter(user=user)
        .select_related("category")
        .annotate(used=Coalesce(Subquery(spent, output_field=MONEY_FIELD), ZERO))
    )
    if on_or_overlapping:
        start, end = on_or_overlapping
        _check_range(start, end)
        # two periods overlap when each starts on/before the other ends
        qs = qs.filter(start_date__lte=end, end_date__gte=start)

    budgets = list(qs.order_by("start_date", "category__name"))
    for b in budgets:
        b.remaining = b.limit_amount - b.used
        b.used_pct = (b.used * 100 / b.limit_amount).quantize(Decimal("0.01"))
        b.is_over = b.remaining < 0
    return budgets


def overspent_budgets(user, *, on_or_overlapping: tuple[date, date] | None = None) -> list[Budget]:
    """Budgets where spending has gone over the limit (remaining < 0)."""
    return [b for b in budgets_with_usage(user, on_or_overlapping=on_or_overlapping) if b.is_over]


# --------------------------------------------------------------------------- #
# Savings goals (GET /goals)
# --------------------------------------------------------------------------- #
def goals_with_progress(user, *, status: str | None = None) -> QuerySet:
    """Goals annotated with `contributed`, `progress_pct` (the real, uncapped
    percentage), `bar_pct` (capped at 100 for the progress bar) and
    `remaining_to_target` (never negative)."""
    qs = (
        SavingsGoal.objects.filter(user=user)
        .annotate(contributed=Coalesce(Sum("contributions__amount"), ZERO))
        .annotate(
            progress_pct=Round(
                ExpressionWrapper(F("contributed") * 100 / F("target_amount"), output_field=MONEY_FIELD), 2
            ),
        )
        .annotate(
            bar_pct=Least(F("progress_pct"), Value(Decimal("100.00"), output_field=MONEY_FIELD)),
            remaining_to_target=Greatest(
                ExpressionWrapper(F("target_amount") - F("contributed"), output_field=MONEY_FIELD),
                Value(Decimal("0.00"), output_field=MONEY_FIELD),
            ),
        )
    )
    if status:
        qs = qs.filter(status=status)
    return qs.order_by("created_at")


def goal_contributions(user, goal_id) -> QuerySet:
    """Contributions for one goal, newest first. Filtering by BOTH goal and user
    means a guessed goal id belonging to someone else returns nothing."""
    return GoalContribution.objects.filter(user=user, goal_id=goal_id).order_by(
        "-contribution_date", "-created_at"
    )


# --------------------------------------------------------------------------- #
# Insight inputs (GET /insights) - facts the rule engine reads
# --------------------------------------------------------------------------- #
def category_spend_vs_previous(user, start: date, end: date) -> list[dict]:
    """For each expense category: spend in [start, end] versus the equally long
    period immediately before it. The rule engine can flag, for example,
    "Food spending is 40% higher than the previous period"."""
    _check_range(start, end)
    length = (end - start).days + 1
    prev_end = date.fromordinal(start.toordinal() - 1)
    prev_start = date.fromordinal(prev_end.toordinal() - length + 1)

    rows = (
        Transaction.objects.filter(
            user=user, type="expense", transaction_date__gte=prev_start, transaction_date__lte=end
        )
        .values("category_id", "category__name")
        .annotate(
            current=Coalesce(Sum("amount", filter=Q(transaction_date__gte=start)), ZERO),
            previous=Coalesce(Sum("amount", filter=Q(transaction_date__lte=prev_end)), ZERO),
        )
        .order_by("category__name")
    )
    out = []
    for r in rows:
        r["change_pct"] = (
            ((r["current"] - r["previous"]) / r["previous"] * 100).quantize(Decimal("0.1"))
            if r["previous"] else None   # None = no earlier spending to compare with
        )
        out.append(r)
    return out
