"""Load FICTIONAL demo data for demo@smartbudget.test and print the result of every
query in core/queries.py. Safe to re-run (the demo user's data is rebuilt each time).

    python manage.py demo_queries
"""
from datetime import date
from decimal import Decimal as D

from django.core.management.base import BaseCommand
from django.db import transaction

from core import queries as q
from core.models import Budget, Category, GoalContribution, SavingsGoal, Transaction, User

EMAIL = "demo@smartbudget.test"


class Command(BaseCommand):
    help = "Create fictional demo data and print the output of the ORM queries"

    @transaction.atomic
    def handle(self, *a, **kw):
        User.objects.filter(email=EMAIL).delete()          # cascades to the demo user's rows
        u = User.objects.create_user(EMAIL, "demo-password-123")
        C = {c.name: c for c in Category.objects.filter(user=None)}

        for amount, cat, typ, d in [
            ("4500.00", "Salary", "income", date(2026, 10, 1)),
            ("300.00", "Allowance", "income", date(2026, 10, 12)),
            ("1200.00", "Rent", "expense", date(2026, 10, 2)),
            ("450.00", "Food", "expense", date(2026, 10, 4)),
            ("380.50", "Food", "expense", date(2026, 10, 18)),
            ("220.00", "Transport", "expense", date(2026, 10, 9)),
            ("150.00", "Airtime & Data", "expense", date(2026, 10, 14)),
            ("4500.00", "Salary", "income", date(2026, 9, 1)),
            ("1200.00", "Rent", "expense", date(2026, 9, 2)),
            ("500.00", "Food", "expense", date(2026, 9, 10)),
            ("180.00", "Transport", "expense", date(2026, 9, 15)),
        ]:
            Transaction.objects.create(user=u, category=C[cat], type=typ, amount=D(amount), transaction_date=d)

        for cat, limit in [("Food", "700.00"), ("Transport", "300.00"), ("Rent", "1200.00")]:
            Budget.objects.create(user=u, category=C[cat], period_type="monthly",
                                  start_date=date(2026, 10, 1), end_date=date(2026, 10, 31), limit_amount=D(limit))

        laptop = SavingsGoal.objects.create(user=u, name="Laptop", target_amount=D("8000.00"))
        trip = SavingsGoal.objects.create(user=u, name="Graduation trip", target_amount=D("1000.00"))
        for g, amt, d in [(laptop, "1500.00", date(2026, 9, 5)), (laptop, "1000.00", date(2026, 10, 5)),
                          (trip, "1000.00", date(2026, 10, 6)), (trip, "250.00", date(2026, 10, 15))]:
            GoalContribution.objects.create(goal=g, user=u, amount=D(amt), contribution_date=d)

        start, end = date(2026, 10, 1), date(2026, 10, 31)
        out = self.stdout.write
        out(f"\n=== dashboard_totals {start} .. {end}")
        for k, v in q.dashboard_totals(u, start, end).items():
            out(f"  {k:15} {v:>10}")

        out("\n=== totals_by_category (expenses)")
        for r in q.totals_by_category(u, start, end):
            out(f"  {r['category__name']:16} {r['total']:>10}  {r['share_pct']:>5}%")

        out("\n=== cash_flow_trend (monthly, Sep-Oct)")
        for r in q.cash_flow_trend(u, date(2026, 9, 1), end, "month"):
            out(f"  {r['period']:%Y-%m}  income {r['income']:>9}  expense {r['expense']:>9}  net {r['net']:>9}")

        out("\n=== budgets_with_usage")
        for b in q.budgets_with_usage(u):
            flag = "OVER" if b.is_over else "ok"
            out(f"  {b.category.name:10} limit {b.limit_amount:>8}  used {b.used:>8}  remaining {b.remaining:>8}  {b.used_pct:>6}%  {flag}")

        out("\n=== goals_with_progress")
        for g in q.goals_with_progress(u):
            out(f"  {g.name:15} {g.contributed:>8} / {g.target_amount:>8}  real {g.progress_pct:>6}%  bar {g.bar_pct:>6}%  left {g.remaining_to_target:>8}")

        out("\n=== category_spend_vs_previous (Oct vs Sep)")
        for r in q.category_spend_vs_previous(u, start, end):
            chg = "n/a" if r["change_pct"] is None else f"{r['change_pct']}%"
            out(f"  {r['category__name']:16} now {r['current']:>8}  before {r['previous']:>8}  change {chg}")

        out(f"\nDemo user: {EMAIL}  (fictional data; rerun the command to reset it)")
