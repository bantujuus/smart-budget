"""Tests for the budget and savings-goal endpoints."""
from decimal import Decimal

from rest_framework.test import APIClient

from core.models import Budget, Category, GoalContribution, SavingsGoal
from core.test_api_finance import FinanceApiBase


class BudgetApiTests(FinanceApiBase):
    def budget_body(self, **kw):
        body = {"category_id": str(self.food.id), "period_type": "monthly",
                "start_date": "2026-10-01", "end_date": "2026-10-31", "limit_amount": "500.00"}
        body.update(kw)
        return body

    def create_budget(self, **kw):
        return self.client.post("/api/v1/budgets/", self.budget_body(**kw), format="json")

    def test_create_budget_returns_usage_figures(self):
        self.make_tx(amount="125.50", transaction_date="2026-10-08")
        r = self.create_budget()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["limit_amount"], "500.00")
        self.assertEqual(r.data["used"], "125.50")
        self.assertEqual(r.data["remaining"], "374.50")
        self.assertFalse(r.data["is_over"])

    def test_overspending_is_flagged(self):
        self.make_tx(amount="600.00", transaction_date="2026-10-08")
        r = self.create_budget()
        self.assertTrue(r.data["is_over"])
        self.assertEqual(r.data["remaining"], "-100.00")

    def test_overlapping_budget_is_a_conflict(self):
        self.create_budget()
        r = self.create_budget(start_date="2026-10-15", end_date="2026-11-15")
        self.assertEqual(r.status_code, 409)

    def test_income_category_is_rejected(self):
        r = self.create_budget(category_id=str(self.salary.id))
        self.assertEqual(r.status_code, 400)

    def test_bad_limit_and_dates_are_rejected(self):
        self.assertEqual(self.create_budget(limit_amount="0").status_code, 400)
        self.assertEqual(self.create_budget(start_date="2026-10-31", end_date="2026-10-01").status_code, 400)
        self.assertEqual(self.create_budget(period_type="yearly").status_code, 400)

    def test_list_is_owner_scoped_and_filterable(self):
        self.create_budget()
        bob = self.browser_for(self.bob)
        bob.post("/api/v1/budgets/", self.budget_body(), format="json")
        self.assertEqual(len(self.client.get("/api/v1/budgets/").data), 1)
        inside = self.client.get("/api/v1/budgets/", {"start_date": "2026-10-10", "end_date": "2026-10-12"})
        outside = self.client.get("/api/v1/budgets/", {"start_date": "2026-12-01", "end_date": "2026-12-31"})
        self.assertEqual(len(inside.data), 1)
        self.assertEqual(len(outside.data), 0)

    def test_filter_needs_both_dates(self):
        r = self.client.get("/api/v1/budgets/", {"start_date": "2026-10-10"})
        self.assertEqual(r.status_code, 400)

    def test_patch_limit(self):
        budget_id = self.create_budget().data["id"]
        r = self.client.patch(f"/api/v1/budgets/{budget_id}/", {"limit_amount": "800.00"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["limit_amount"], "800.00")

    def test_patch_into_an_overlap_is_a_conflict(self):
        self.create_budget()
        other = self.create_budget(start_date="2026-11-01", end_date="2026-11-30").data["id"]
        r = self.client.patch(f"/api/v1/budgets/{other}/", {"start_date": "2026-10-20"}, format="json")
        self.assertEqual(r.status_code, 409)

    def test_delete_budget(self):
        budget_id = self.create_budget().data["id"]
        self.assertEqual(self.client.delete(f"/api/v1/budgets/{budget_id}/").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/v1/budgets/{budget_id}/").status_code, 404)

    def test_cannot_touch_another_users_budget(self):
        bob = self.browser_for(self.bob)
        theirs = bob.post("/api/v1/budgets/", self.budget_body(), format="json").data["id"]
        self.assertEqual(self.client.patch(f"/api/v1/budgets/{theirs}/", {"limit_amount": "1.00"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/v1/budgets/{theirs}/").status_code, 404)
        self.assertTrue(Budget.objects.filter(id=theirs).exists())

    def test_requires_login(self):
        self.assertIn(APIClient().get("/api/v1/budgets/").status_code, (401, 403))


class GoalApiTests(FinanceApiBase):
    def create_goal(self, **kw):
        body = {"name": "Laptop", "target_amount": "1000.00"}
        body.update(kw)
        return self.client.post("/api/v1/goals/", body, format="json")

    def contribute(self, goal_id, amount="100.00", client=None):
        return (client or self.client).post(
            f"/api/v1/goals/{goal_id}/contributions/",
            {"amount": amount, "contribution_date": "2026-10-10"}, format="json")

    def test_create_goal(self):
        r = self.create_goal(target_date="2027-03-01")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["status"], "active")
        self.assertEqual(r.data["contributed"], "0.00")
        self.assertEqual(r.data["progress_pct"], "0.00")

    def test_create_goal_with_initial_contribution(self):
        r = self.create_goal(initial_contribution="250.00")
        self.assertEqual(r.data["contributed"], "250.00")
        self.assertEqual(r.data["progress_pct"], "25.00")

    def test_bad_goal_is_rejected(self):
        self.assertEqual(self.create_goal(target_amount="0").status_code, 400)
        self.assertEqual(self.create_goal(name="  ").status_code, 400)
        self.assertEqual(self.create_goal(target_date="01/03/2027").status_code, 400)

    def test_contribution_updates_progress(self):
        goal_id = self.create_goal().data["id"]
        r = self.contribute(goal_id, "100.00")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["goal"]["contributed"], "100.00")
        self.assertEqual(r.data["goal"]["progress_pct"], "10.00")
        self.assertEqual(r.data["goal"]["remaining_to_target"], "900.00")

    def test_goal_completes_when_funded_and_then_refuses_money(self):
        goal_id = self.create_goal(target_amount="100.00").data["id"]
        r = self.contribute(goal_id, "100.00")
        self.assertEqual(r.data["goal"]["status"], "completed")
        again = self.contribute(goal_id, "10.00")
        self.assertEqual(again.status_code, 409)

    def test_deleting_a_contribution_reopens_the_goal(self):
        goal_id = self.create_goal(target_amount="100.00").data["id"]
        cid = self.contribute(goal_id, "100.00").data["contribution"]["id"]
        self.assertEqual(self.client.delete(f"/api/v1/goals/{goal_id}/contributions/{cid}/").status_code, 204)
        self.assertEqual(self.client.get(f"/api/v1/goals/{goal_id}/").data["status"], "active")

    def test_list_contributions(self):
        goal_id = self.create_goal().data["id"]
        self.contribute(goal_id, "10.00")
        self.contribute(goal_id, "20.00")
        self.assertEqual(len(self.client.get(f"/api/v1/goals/{goal_id}/contributions/").data), 2)

    def test_status_changes(self):
        goal_id = self.create_goal().data["id"]
        ok = self.client.patch(f"/api/v1/goals/{goal_id}/", {"status": "paused"}, format="json")
        self.assertEqual(ok.data["status"], "paused")
        self.assertEqual(self.contribute(goal_id).status_code, 409)       # paused goals take no money
        bad = self.client.patch(f"/api/v1/goals/{goal_id}/", {"status": "completed"}, format="json")
        self.assertEqual(bad.status_code, 409)                             # paused -> completed is not allowed
        junk = self.client.patch(f"/api/v1/goals/{goal_id}/", {"status": "banana"}, format="json")
        self.assertEqual(junk.status_code, 400)

    def test_list_filters_by_status(self):
        a = self.create_goal(name="A").data["id"]
        self.create_goal(name="B")
        self.client.patch(f"/api/v1/goals/{a}/", {"status": "archived"}, format="json")
        self.assertEqual(len(self.client.get("/api/v1/goals/").data), 2)
        self.assertEqual(len(self.client.get("/api/v1/goals/", {"status": "active"}).data), 1)

    def test_goals_are_private(self):
        bob = self.browser_for(self.bob)
        theirs = bob.post("/api/v1/goals/", {"name": "Secret", "target_amount": "500.00"}, format="json").data["id"]
        self.assertEqual(len(self.client.get("/api/v1/goals/").data), 0)
        self.assertEqual(self.client.get(f"/api/v1/goals/{theirs}/").status_code, 404)
        self.assertEqual(self.client.patch(f"/api/v1/goals/{theirs}/", {"status": "paused"}, format="json").status_code, 404)
        self.assertEqual(self.contribute(theirs).status_code, 404)
        self.assertEqual(self.client.get(f"/api/v1/goals/{theirs}/contributions/").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/goals/not-a-uuid/").status_code, 404)
        self.assertEqual(SavingsGoal.objects.get(id=theirs).status, "active")
        self.assertEqual(GoalContribution.objects.count(), 0)

    def test_requires_login(self):
        self.assertIn(APIClient().get("/api/v1/goals/").status_code, (401, 403))