"""Rule-based smart insights (FR-13, UC-11).

Each rule is a small function that looks at the user's own records for the chosen period
and returns zero or more insights. Every insight says WHICH rule fired, WHY (the numbers
and the threshold), and for WHICH period, so it is explainable and never presented as
financial advice (NFR-10). No AI is used: the same data always gives the same insights.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from . import queries

# Thresholds (change them here; the explanation text reads them automatically)
NEAR_LIMIT_PCT = Decimal("80")      # budget at or above this % of its limit
SPIKE_PCT = Decimal("30")           # category spend this % higher than the previous period
SPIKE_MIN_AMOUNT = Decimal("50.00")  # ignore tiny categories so small numbers don't cause noise
SAVINGS_GOOD_PCT = Decimal("20")    # saved at least this % of income
GOAL_NEAR_PCT = Decimal("90")       # goal funded to at least this %

DISCLAIMER = (
    "These tips are automatic summaries of your own records. They are for learning and "
    "planning only, and are not financial advice."
)

SEVERITY_ORDER = {"warning": 0, "info": 1, "positive": 2}


def _insight(rule, severity, title, message, explanation, start, end, data=None):
    return {
        "rule": rule,
        "severity": severity,
        "title": title,
        "message": message,
        "explanation": explanation,
        "period": {"start_date": start, "end_date": end},
        "data": data or {},
    }


def _budget_rules(user, start, end, money):
    out = []
    for b in queries.budgets_with_usage(user, on_or_overlapping=(start, end)):
        data = {"budget_id": b.id, "category": b.category.name, "used": b.used,
                "limit_amount": b.limit_amount, "used_pct": b.used_pct}
        if b.is_over:
            out.append(_insight(
                "BUDGET_OVER", "warning",
                f"{b.category.name} budget exceeded",
                f"You have spent {money(b.used)} of your {money(b.limit_amount)} {b.category.name} "
                f"budget, which is {money(-b.remaining)} over the limit.",
                "Shown when spending in a budget's category is above the budget's limit.",
                b.start_date, b.end_date, data))
        elif b.used_pct >= NEAR_LIMIT_PCT:
            out.append(_insight(
                "BUDGET_NEAR_LIMIT", "info",
                f"{b.category.name} budget almost used up",
                f"You have used {b.used_pct}% of your {b.category.name} budget "
                f"({money(b.used)} of {money(b.limit_amount)}).",
                f"Shown when a budget is at {NEAR_LIMIT_PCT}% or more of its limit but not over it.",
                b.start_date, b.end_date, data))
    return out


def _spend_change_rules(user, start, end, money):
    out = []
    length = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=length - 1)
    for r in queries.category_spend_vs_previous(user, start, end):
        change = r["change_pct"]
        if change is not None and change >= SPIKE_PCT and r["current"] >= SPIKE_MIN_AMOUNT:
            name = r["category__name"]
            out.append(_insight(
                "CATEGORY_SPEND_UP", "info",
                f"{name} spending is up",
                f"You spent {money(r['current'])} on {name}, which is {change}% more than the "
                f"{money(r['previous'])} spent in the previous period ({prev_start} to {prev_end}).",
                f"Shown when a category's spending is at least {SPIKE_PCT}% higher than the previous "
                f"period of the same length (and at least {money(SPIKE_MIN_AMOUNT)}).",
                start, end,
                {"category": name, "current": r["current"], "previous": r["previous"], "change_pct": change}))
    return out


def _cash_flow_rules(user, start, end, money):
    t = queries.dashboard_totals(user, start, end)
    income, expense, net = t["income_total"], t["expense_total"], t["net_cash_flow"]
    data = {"income_total": income, "expense_total": expense, "net_cash_flow": net}
    if net < 0:
        return [_insight(
            "NEGATIVE_CASH_FLOW", "warning", "You spent more than you recorded as income",
            f"Recorded expenses ({money(expense)}) were {money(-net)} higher than recorded income "
            f"({money(income)}) in this period.",
            "Shown when expenses are higher than income in the selected period. "
            "This uses recorded transactions only, not a bank balance.",
            start, end, data)]
    if income > 0:
        rate = (net * 100 / income).quantize(Decimal("0.1"))
        if rate >= SAVINGS_GOOD_PCT:
            return [_insight(
                "GOOD_SAVINGS_RATE", "positive", "Good savings rate",
                f"You kept {rate}% of your recorded income ({money(net)} of {money(income)}) in this period.",
                f"Shown when income minus expenses is at least {SAVINGS_GOOD_PCT}% of income.",
                start, end, {**data, "savings_rate_pct": rate})]
    return []


def _goal_rules(user, start, end, money):
    out = []
    today = timezone.localdate()
    for g in queries.goals_with_progress(user, status="active"):
        data = {"goal_id": g.id, "name": g.name, "contributed": g.contributed,
                "target_amount": g.target_amount, "progress_pct": g.progress_pct}
        if GOAL_NEAR_PCT <= g.progress_pct < 100:
            out.append(_insight(
                "GOAL_NEARLY_THERE", "positive", f"'{g.name}' is almost funded",
                f"You have saved {money(g.contributed)} of {money(g.target_amount)} ({g.progress_pct}%). "
                f"Only {money(g.remaining_to_target)} to go.",
                f"Shown when an active goal is at least {GOAL_NEAR_PCT}% funded but not complete.",
                start, end, data))
        elif g.target_date and g.target_date < today and g.progress_pct < 100:
            out.append(_insight(
                "GOAL_PAST_TARGET_DATE", "warning", f"'{g.name}' passed its target date",
                f"The target date ({g.target_date}) has passed and the goal is {g.progress_pct}% funded "
                f"({money(g.contributed)} of {money(g.target_amount)}).",
                "Shown when an active goal is not fully funded and its target date is in the past.",
                start, end, data))
    return out


def build_insights(user, start: date, end: date) -> dict:
    """All insights for the period, most important first."""
    if not queries.list_transactions(user, start=start, end=end).exists():
        return {"insights": [], "message": "Not enough data for this period. Record some transactions to get tips.",
                "disclaimer": DISCLAIMER}

    def money(value):
        return f"{user.currency} {Decimal(value):,.2f}"

    found = []
    for rule in (_budget_rules, _spend_change_rules, _cash_flow_rules, _goal_rules):
        found.extend(rule(user, start, end, money))
    found.sort(key=lambda i: SEVERITY_ORDER[i["severity"]])  # stable: keeps rule order inside a group
    message = "" if found else "No tips for this period: nothing unusual in your records."
    return {"insights": found, "message": message, "disclaimer": DISCLAIMER}