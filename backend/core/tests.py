"""Tests for core/queries.py. Run:  python manage.py test core -v 2
They run on a throwaway PostgreSQL test database, so your real data is untouched."""
from datetime import date
from decimal import Decimal as D

from django.test import TestCase

from . import queries as q
from .models import Budget, Category, GoalContribution, SavingsGoal, Transaction, User


def cat(name, kind):
    return Category.objects.create(user=None, name=name, kind=kind)


class QueryTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = User.objects.create_user("a@test.zm", "x")
        cls.b = User.objects.create_user("b@test.zm", "x")
        cls.salary = cat("Salary", "income")
        cls.food = cat("Food", "expense")
        cls.rent = cat("Rent", "expense")

    def tx(self, user, category, type, amount, d):
        return Transaction.objects.create(
            user=user, category=category, type=type, amount=D(amount), transaction_date=d
        )


class DashboardTotalsTests(QueryTestBase):
    def setUp(self):
        self.tx(self.a, self.salary, "income", "5000.00", date(2026, 10, 1))
        self.tx(self.a, self.food, "expense", "125.50", date(2026, 10, 3))
        self.tx(self.a, self.rent, "expense", "1500.00", date(2026, 10, 31))
        self.tx(self.a, self.food, "expense", "99.99", date(2026, 11, 1))    # outside range
        self.tx(self.a, self.food, "expense", "10.00", date(2026, 9, 30))    # outside range
        self.tx(self.b, self.salary, "income", "999999.00", date(2026, 10, 5))  # someone else

    def test_totals_and_net(self):
        t = q.dashboard_totals(self.a, date(2026, 10, 1), date(2026, 10, 31))
        self.assertEqual(t["income_total"], D("5000.00"))
        self.assertEqual(t["expense_total"], D("1625.50"))
        self.assertEqual(t["net_cash_flow"], D("3374.50"))

    def test_range_is_inclusive_on_both_ends(self):
        t = q.dashboard_totals(self.a, date(2026, 10, 31), date(2026, 10, 31))
        self.assertEqual(t["expense_total"], D("1500.00"))

    def test_empty_period_is_zero_not_none(self):
        t = q.dashboard_totals(self.a, date(2020, 1, 1), date(2020, 1, 31))
        self.assertEqual((t["income_total"], t["expense_total"], t["net_cash_flow"]),
                         (D("0.00"), D("0.00"), D("0.00")))

    def test_other_users_data_is_never_included(self):
        t = q.dashboard_totals(self.b, date(2026, 10, 1), date(2026, 10, 31))
        self.assertEqual(t["income_total"], D("999999.00"))
        self.assertEqual(t["expense_total"], D("0.00"))

    def test_money_is_decimal_and_exact(self):
        for i in range(10):
            self.tx(self.b, self.food, "expense", "0.10", date(2026, 10, 6))
        t = q.dashboard_totals(self.b, date(2026, 10, 1), date(2026, 10, 31))
        self.assertIsInstance(t["expense_total"], D)
        self.assertEqual(t["expense_total"], D("1.00"))   # float would give 0.9999999...

    def test_bad_range_rejected(self):
        with self.assertRaises(ValueError):
            q.dashboard_totals(self.a, date(2026, 10, 2), date(2026, 10, 1))

    def test_single_query(self):
        with self.assertNumQueries(1):
            q.dashboard_totals(self.a, date(2026, 10, 1), date(2026, 10, 31))


class ReportTests(QueryTestBase):
    def setUp(self):
        self.tx(self.a, self.food, "expense", "300.00", date(2026, 10, 2))
        self.tx(self.a, self.food, "expense", "100.00", date(2026, 10, 20))
        self.tx(self.a, self.rent, "expense", "600.00", date(2026, 10, 5))
        self.tx(self.a, self.salary, "income", "2000.00", date(2026, 10, 1))
        self.tx(self.a, self.salary, "income", "2000.00", date(2026, 11, 1))
        self.tx(self.a, self.food, "expense", "50.00", date(2026, 11, 3))

    def test_by_category_sorted_with_shares(self):
        rows = q.totals_by_category(self.a, date(2026, 10, 1), date(2026, 10, 31))
        self.assertEqual([r["category__name"] for r in rows], ["Rent", "Food"])
        self.assertEqual([r["total"] for r in rows], [D("600.00"), D("400.00")])
        self.assertEqual([r["share_pct"] for r in rows], [D("60.0"), D("40.0")])

    def test_by_category_no_data(self):
        self.assertEqual(q.totals_by_category(self.a, date(2020, 1, 1), date(2020, 1, 31)), [])

    def test_monthly_trend(self):
        rows = q.cash_flow_trend(self.a, date(2026, 10, 1), date(2026, 11, 30), "month")
        self.assertEqual(len(rows), 2)
        self.assertEqual((rows[0]["income"], rows[0]["expense"], rows[0]["net"]),
                         (D("2000.00"), D("1000.00"), D("1000.00")))
        self.assertEqual((rows[1]["income"], rows[1]["expense"], rows[1]["net"]),
                         (D("2000.00"), D("50.00"), D("1950.00")))

    def test_trend_bad_granularity(self):
        with self.assertRaises(ValueError):
            q.cash_flow_trend(self.a, date(2026, 10, 1), date(2026, 10, 31), "year")


class BudgetTests(QueryTestBase):
    def setUp(self):
        self.oct_food = Budget.objects.create(
            user=self.a, category=self.food, period_type="monthly",
            start_date=date(2026, 10, 1), end_date=date(2026, 10, 31), limit_amount=D("400.00"))
        self.oct_rent = Budget.objects.create(
            user=self.a, category=self.rent, period_type="monthly",
            start_date=date(2026, 10, 1), end_date=date(2026, 10, 31), limit_amount=D("2000.00"))
        self.tx(self.a, self.food, "expense", "250.00", date(2026, 10, 2))
        self.tx(self.a, self.food, "expense", "250.00", date(2026, 10, 31))   # boundary day counts
        self.tx(self.a, self.food, "expense", "999.00", date(2026, 11, 1))    # outside period
        self.tx(self.a, self.rent, "expense", "1500.00", date(2026, 10, 5))
        self.tx(self.b, self.food, "expense", "777.00", date(2026, 10, 3))    # other user, same category
        self.tx(self.a, self.salary, "income", "5000.00", date(2026, 10, 1))  # income never counts

    def by_name(self):
        return {b.category.name: b for b in q.budgets_with_usage(self.a)}

    def test_used_remaining_and_overspend(self):
        r = self.by_name()
        self.assertEqual((r["Food"].used, r["Food"].remaining), (D("500.00"), D("-100.00")))
        self.assertEqual(r["Food"].used_pct, D("125.00"))
        self.assertEqual((r["Rent"].used, r["Rent"].remaining), (D("1500.00"), D("500.00")))

    def test_budget_with_no_spending_is_zero(self):
        Budget.objects.create(user=self.a, category=self.food, period_type="monthly",
                              start_date=date(2026, 12, 1), end_date=date(2026, 12, 31),
                              limit_amount=D("300.00"))
        dec = [b for b in q.budgets_with_usage(self.a) if b.start_date.month == 12][0]
        self.assertEqual((dec.used, dec.remaining), (D("0.00"), D("300.00")))

    def test_overspent_only_returns_over_limit(self):
        names = [b.category.name for b in q.overspent_budgets(self.a)]
        self.assertEqual(names, ["Food"])

    def test_period_filter(self):
        self.assertEqual(len(q.budgets_with_usage(self.a, on_or_overlapping=(date(2027, 1, 1), date(2027, 1, 31)))), 0)
        self.assertEqual(len(q.budgets_with_usage(self.a, on_or_overlapping=(date(2026, 10, 15), date(2026, 11, 15)))), 2)

    def test_other_users_budgets_hidden(self):
        self.assertEqual(q.budgets_with_usage(self.b), [])

    def test_no_n_plus_one(self):
        # 1 query for all budgets, their usage AND category names
        with self.assertNumQueries(1):
            for b in q.budgets_with_usage(self.a):
                _ = (b.category.name, b.used, b.remaining)


class GoalTests(QueryTestBase):
    def setUp(self):
        self.laptop = SavingsGoal.objects.create(user=self.a, name="Laptop", target_amount=D("8000.00"))
        self.trip = SavingsGoal.objects.create(user=self.a, name="Trip", target_amount=D("1000.00"))
        self.empty = SavingsGoal.objects.create(user=self.a, name="Empty", target_amount=D("500.00"))
        for amt in ("2000.00", "500.00"):
            GoalContribution.objects.create(goal=self.laptop, user=self.a, amount=D(amt), contribution_date=date(2026, 10, 1))
        for amt in ("800.00", "600.00"):   # 1400 > 1000 target
            GoalContribution.objects.create(goal=self.trip, user=self.a, amount=D(amt), contribution_date=date(2026, 10, 2))

    def goals(self, **kw):
        return {g.name: g for g in q.goals_with_progress(self.a, **kw)}

    def test_progress(self):
        g = self.goals()["Laptop"]
        self.assertEqual((g.contributed, g.progress_pct, g.bar_pct, g.remaining_to_target),
                         (D("2500.00"), D("31.25"), D("31.25"), D("5500.00")))

    def test_over_target_caps_bar_but_keeps_real_total(self):
        g = self.goals()["Trip"]
        self.assertEqual(g.contributed, D("1400.00"))
        self.assertEqual(g.progress_pct, D("140.00"))
        self.assertEqual(g.bar_pct, D("100.00"))
        self.assertEqual(g.remaining_to_target, D("0.00"))

    def test_goal_without_contributions_is_zero(self):
        g = self.goals()["Empty"]
        self.assertEqual((g.contributed, g.progress_pct), (D("0.00"), D("0.00")))

    def test_status_filter_and_owner_isolation(self):
        self.trip.status = "completed"; self.trip.save()
        self.assertEqual(list(self.goals(status="completed")), ["Trip"])
        self.assertEqual(q.goals_with_progress(self.b).count(), 0)

    def test_contributions_cannot_be_read_with_another_users_session(self):
        self.assertEqual(q.goal_contributions(self.a, self.laptop.id).count(), 2)
        self.assertEqual(q.goal_contributions(self.b, self.laptop.id).count(), 0)

    def test_single_query_for_all_goals(self):
        with self.assertNumQueries(1):
            list(q.goals_with_progress(self.a))


class TransactionListTests(QueryTestBase):
    def setUp(self):
        self.tx(self.a, self.food, "expense", "10.00", date(2026, 10, 1))
        self.tx(self.a, self.food, "expense", "20.00", date(2026, 10, 15))
        self.tx(self.a, self.salary, "income", "100.00", date(2026, 10, 10))
        self.tx(self.b, self.food, "expense", "30.00", date(2026, 10, 10))

    def test_filters_and_ordering(self):
        rows = list(q.list_transactions(self.a, type="expense", start=date(2026, 10, 2)))
        self.assertEqual([r.amount for r in rows], [D("20.00")])
        all_rows = list(q.list_transactions(self.a))
        self.assertEqual([r.transaction_date for r in all_rows],
                         [date(2026, 10, 15), date(2026, 10, 10), date(2026, 10, 1)])

    def test_no_n_plus_one_on_category_name(self):
        with self.assertNumQueries(1):
            for t in q.list_transactions(self.a):
                _ = t.category.name

    def test_cannot_see_other_users_rows(self):
        self.assertEqual(q.list_transactions(self.a).filter(amount=D("30.00")).count(), 0)


class InsightInputTests(QueryTestBase):
    def test_change_vs_previous_period(self):
        # previous period: Sep 1-30 ; current: Oct 1-30 (equal 30-day lengths)
        self.tx(self.a, self.food, "expense", "100.00", date(2026, 9, 10))
        self.tx(self.a, self.food, "expense", "140.00", date(2026, 10, 10))
        self.tx(self.a, self.rent, "expense", "500.00", date(2026, 10, 10))   # no previous spend
        rows = {r["category__name"]: r for r in q.category_spend_vs_previous(self.a, date(2026, 10, 1), date(2026, 10, 30))}
        self.assertEqual(rows["Food"]["change_pct"], D("40.0"))
        self.assertIsNone(rows["Rent"]["change_pct"])
