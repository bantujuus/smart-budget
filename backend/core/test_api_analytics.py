"""Tests for the dashboard, reports and insights endpoints."""
import calendar

from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Category
from core.test_api_finance import FinanceApiBase

OCT = {"start_date": "2026-10-01", "end_date": "2026-10-31"}


class AnalyticsBase(FinanceApiBase):
    def spend(self, amount, day="2026-10-10", category=None, user=None):
        return self.make_tx(user=user, amount=amount, transaction_date=day, category=category or self.food)

    def earn(self, amount, day="2026-10-02", user=None):
        return self.make_tx(user=user, type="income", category=self.salary, amount=amount, transaction_date=day)

    def budget(self, limit="500.00", **kw):
        body = {"category_id": str(self.food.id), "period_type": "monthly", "start_date": "2026-10-01",
                "end_date": "2026-10-31", "limit_amount": limit}
        body.update(kw)
        return self.client.post("/api/v1/budgets/", body, format="json")


class DashboardApiTests(AnalyticsBase):
    def test_totals_match_the_records(self):
        self.earn("1000.00")
        self.spend("125.50")
        self.spend("74.50", day="2026-10-20")
        r = self.client.get("/api/v1/dashboard/", OCT)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["totals"]["income_total"], "1000.00")
        self.assertEqual(r.json()["totals"]["expense_total"], "200.00")
        self.assertEqual(r.json()["totals"]["net_cash_flow"], "800.00")

    def test_period_is_inclusive_and_ignores_other_months(self):
        self.spend("10.00", day="2026-10-01")
        self.spend("20.00", day="2026-10-31")
        self.spend("999.00", day="2026-09-30")
        self.spend("999.00", day="2026-11-01")
        self.assertEqual(self.client.get("/api/v1/dashboard/", OCT).json()["totals"]["expense_total"], "30.00")

    def test_includes_budgets_goals_and_recent_transactions(self):
        self.spend("125.50")
        self.budget()
        self.client.post("/api/v1/goals/", {"name": "Laptop", "target_amount": "1000.00"}, format="json")
        r = self.client.get("/api/v1/dashboard/", OCT)
        self.assertEqual(r.json()["budgets"][0]["used"], "125.50")
        self.assertEqual(r.json()["goals"][0]["name"], "Laptop")
        self.assertEqual(len(r.json()["recent_transactions"]), 1)

    def test_recent_transactions_are_limited_to_five(self):
        for _ in range(7):
            self.spend("1.00")
        self.assertEqual(len(self.client.get("/api/v1/dashboard/", OCT).json()["recent_transactions"]), 5)

    def test_defaults_to_the_current_month(self):
        r = self.client.get("/api/v1/dashboard/")
        today = timezone.localdate()
        self.assertEqual(r.json()["period"]["start_date"], today.replace(day=1).isoformat())
        last = calendar.monthrange(today.year, today.month)[1]
        self.assertEqual(r.json()["period"]["end_date"], today.replace(day=last).isoformat())

    def test_empty_state_is_all_zero(self):
        r = self.client.get("/api/v1/dashboard/", OCT)
        self.assertEqual(r.json()["totals"]["net_cash_flow"], "0.00")
        self.assertEqual(r.json()["budgets"], [])
        self.assertEqual(r.json()["recent_transactions"], [])

    def test_bad_ranges_are_rejected(self):
        self.assertEqual(self.client.get("/api/v1/dashboard/", {"start_date": "2026-10-31", "end_date": "2026-10-01"}).status_code, 400)
        self.assertEqual(self.client.get("/api/v1/dashboard/", {"start_date": "2026-10-01"}).status_code, 400)
        self.assertEqual(self.client.get("/api/v1/dashboard/", {"start_date": "yesterday", "end_date": "today"}).status_code, 400)

    def test_only_own_data(self):
        self.spend("50.00", user=self.bob)
        self.assertEqual(self.client.get("/api/v1/dashboard/", OCT).json()["totals"]["expense_total"], "0.00")

    def test_requires_login(self):
        self.assertIn(APIClient().get("/api/v1/dashboard/").status_code, (401, 403))


class ReportApiTests(AnalyticsBase):
    def test_summary_by_category_with_shares(self):
        transport = Category.objects.create(user=None, name="Transport", kind="expense")
        self.spend("300.00")
        self.spend("100.00", category=transport)
        self.earn("1000.00")
        r = self.client.get("/api/v1/reports/summary/", OCT)
        rows = r.json()["expense_by_category"]
        self.assertEqual([x["category"] for x in rows], ["Food", "Transport"])   # largest first
        self.assertEqual(rows[0]["total"], "300.00")
        self.assertEqual(rows[0]["share_pct"], "75.0")
        self.assertEqual(r.json()["income_by_category"][0]["category"], "Salary")
        self.assertEqual(r.json()["totals"]["net_cash_flow"], "600.00")

    def test_trend_by_month_and_day(self):
        self.spend("10.00", day="2026-09-15")
        self.spend("20.00", day="2026-10-15")
        wide = {"start_date": "2026-09-01", "end_date": "2026-10-31"}
        monthly = self.client.get("/api/v1/reports/summary/", wide).json()["trend"]
        self.assertEqual([str(p["period"]) for p in monthly], ["2026-09-01", "2026-10-01"])
        self.assertEqual(monthly[1]["expense"], "20.00")
        daily = self.client.get("/api/v1/reports/summary/", {**wide, "granularity": "day"}).json()["trend"]
        self.assertEqual(len(daily), 2)

    def test_report_agrees_with_dashboard(self):
        self.earn("700.00")
        self.spend("123.45")
        dash = self.client.get("/api/v1/dashboard/", OCT).json()["totals"]
        report = self.client.get("/api/v1/reports/summary/", OCT).json()["totals"]
        self.assertEqual(dash, report)

    def test_bad_input(self):
        url = "/api/v1/reports/summary/"
        self.assertEqual(self.client.get(url, {"start_date": "2026-10-31", "end_date": "2026-10-01"}).status_code, 400)
        self.assertEqual(self.client.get(url, {**OCT, "granularity": "year"}).status_code, 400)
        long_range = {"start_date": "2020-01-01", "end_date": "2026-10-31", "granularity": "day"}
        self.assertEqual(self.client.get(url, long_range).status_code, 400)

    def test_only_own_data(self):
        self.spend("50.00", user=self.bob)
        self.assertEqual(self.client.get("/api/v1/reports/summary/", OCT).json()["expense_by_category"], [])

    def test_requires_login(self):
        self.assertIn(APIClient().get("/api/v1/reports/summary/").status_code, (401, 403))


class InsightsApiTests(AnalyticsBase):
    def rules(self, **params):
        r = self.client.get("/api/v1/insights/", params or OCT)
        self.assertEqual(r.status_code, 200)
        return [i["rule"] for i in r.json()["insights"]], r

    def test_no_transactions_means_not_enough_data(self):
        rules, r = self.rules()
        self.assertEqual(rules, [])
        self.assertIn("Not enough data", r.json()["message"])
        self.assertIn("not financial advice", r.json()["disclaimer"])

    def test_budget_over(self):
        self.spend("600.00")
        self.budget()
        rules, r = self.rules()
        self.assertIn("BUDGET_OVER", rules)
        tip = next(i for i in r.json()["insights"] if i["rule"] == "BUDGET_OVER")
        self.assertEqual(tip["severity"], "warning")
        self.assertIn("ZMW 100.00 over", tip["message"])
        self.assertTrue(tip["explanation"])
        self.assertEqual(tip["period"]["start_date"], "2026-10-01")

    def test_budget_near_limit_but_not_over(self):
        self.spend("420.00")
        self.budget()
        rules, _ = self.rules()
        self.assertIn("BUDGET_NEAR_LIMIT", rules)
        self.assertNotIn("BUDGET_OVER", rules)

    def test_comfortable_budget_gives_no_budget_tip(self):
        self.spend("100.00")
        self.budget()
        rules, _ = self.rules()
        self.assertFalse({"BUDGET_OVER", "BUDGET_NEAR_LIMIT"} & set(rules))

    def test_category_spend_up(self):
        self.spend("100.00", day="2026-09-15")
        self.spend("200.00", day="2026-10-15")
        rules, r = self.rules()
        self.assertIn("CATEGORY_SPEND_UP", rules)
        tip = next(i for i in r.json()["insights"] if i["rule"] == "CATEGORY_SPEND_UP")
        self.assertIn("100.0% more", tip["message"])

    def test_tiny_amounts_do_not_trigger_spend_up(self):
        self.spend("1.00", day="2026-09-15")
        self.spend("5.00", day="2026-10-15")
        rules, _ = self.rules()
        self.assertNotIn("CATEGORY_SPEND_UP", rules)

    def test_negative_cash_flow(self):
        self.earn("100.00")
        self.spend("300.00")
        rules, _ = self.rules()
        self.assertIn("NEGATIVE_CASH_FLOW", rules)

    def test_good_savings_rate(self):
        self.earn("1000.00")
        self.spend("400.00")
        rules, r = self.rules()
        self.assertIn("GOOD_SAVINGS_RATE", rules)
        tip = next(i for i in r.json()["insights"] if i["rule"] == "GOOD_SAVINGS_RATE")
        self.assertEqual(tip["severity"], "positive")

    def test_goal_nearly_funded(self):
        self.spend("10.00")
        self.client.post("/api/v1/goals/", {"name": "Laptop", "target_amount": "1000.00",
                                           "initial_contribution": "950.00"}, format="json")
        rules, _ = self.rules()
        self.assertIn("GOAL_NEARLY_THERE", rules)

    def test_goal_past_target_date(self):
        self.spend("10.00")
        self.client.post("/api/v1/goals/", {"name": "Trip", "target_amount": "1000.00",
                                           "target_date": "2020-01-01"}, format="json")
        rules, _ = self.rules()
        self.assertIn("GOAL_PAST_TARGET_DATE", rules)

    def test_warnings_come_first(self):
        self.earn("1000.00")
        self.spend("600.00")
        self.budget()                      # over budget (warning) and 40% saved (positive)
        _, r = self.rules()
        severities = [i["severity"] for i in r.json()["insights"]]
        self.assertEqual(severities, sorted(severities, key=["warning", "info", "positive"].index))
        self.assertEqual(severities[0], "warning")

    def test_only_own_data(self):
        self.spend("600.00", user=self.bob)
        rules, r = self.rules()
        self.assertEqual(rules, [])
        self.assertIn("Not enough data", r.json()["message"])

    def test_bad_range_and_login(self):
        self.assertEqual(self.client.get("/api/v1/insights/", {"start_date": "2026-10-31", "end_date": "2026-10-01"}).status_code, 400)
        self.assertIn(APIClient().get("/api/v1/insights/").status_code, (401, 403))