"""Tests for core/services.py (transactions, locking, ownership, validation).

    python manage.py test core.test_services -v 2

The concurrency tests open several real PostgreSQL connections at the same time
(one per thread), so they need TransactionTestCase: data must really be committed
for another connection to see it.
"""
import threading
from datetime import date
from decimal import Decimal as D
from unittest import mock

from django.db import connection
from django.test import TestCase, TransactionTestCase

from . import services as s
from .models import Budget, Category, GoalContribution, SavingsGoal, Transaction, User

D1 = date(2026, 10, 1)


def make_world():
    a = User.objects.create_user("a@test.zm", "x")
    b = User.objects.create_user("b@test.zm", "x")
    cats = {
        "salary": Category.objects.create(user=None, name="Salary", kind="income"),
        "food": Category.objects.create(user=None, name="Food", kind="expense"),
        "other": Category.objects.create(user=None, name="Misc", kind="both"),
        "b_private": Category.objects.create(user=b, name="B only", kind="expense"),
    }
    return a, b, cats


class TransactionServiceTests(TestCase):
    def setUp(self):
        self.a, self.b, self.c = make_world()

    def create(self, **kw):
        args = dict(category_id=self.c["food"].id, type="expense", amount="125.50", transaction_date="2026-10-08")
        args.update(kw)
        return s.create_transaction(self.a, **args)

    def test_create_ok_and_owner_is_the_caller(self):
        tx = self.create()
        self.assertEqual((tx.user, tx.amount), (self.a, D("125.50")))

    def test_float_money_is_rejected(self):
        with self.assertRaises(s.ValidationFailed) as cm:
            self.create(amount=0.1)
        self.assertIn("amount", cm.exception.fields)

    def test_bad_amounts(self):
        for bad in ("0", "-5", "abc", "1.234", "NaN", "Infinity", "99999999999"):
            with self.subTest(bad=bad), self.assertRaises(s.ValidationFailed):
                self.create(amount=bad)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_amount_is_stored_with_two_decimals(self):
        self.assertEqual(self.create(amount="5").amount, D("5.00"))

    def test_category_kind_must_match_type(self):
        with self.assertRaises(s.ValidationFailed):
            self.create(category_id=self.c["salary"].id, type="expense")
        self.create(category_id=self.c["other"].id, type="income")       # 'both' fits either

    def test_cannot_use_another_users_category(self):
        with self.assertRaises(s.NotFound):
            self.create(category_id=self.c["b_private"].id)

    def test_cannot_use_archived_category(self):
        mine = s.create_category(self.a, name="Snacks", kind="expense")
        s.archive_category(self.a, mine.id)
        with self.assertRaises(s.NotFound):
            self.create(category_id=mine.id)

    def test_bad_type_and_date(self):
        with self.assertRaises(s.ValidationFailed):
            self.create(type="transfer")
        with self.assertRaises(s.ValidationFailed):
            self.create(transaction_date="08/10/2026")

    def test_update_revalidates_category_against_type(self):
        tx = self.create()
        with self.assertRaises(s.ValidationFailed):
            s.update_transaction(self.a, tx.id, type="income")           # Food is expense-only
        tx.refresh_from_db()
        self.assertEqual(tx.type, "expense")                             # unchanged

    def test_update_rejects_unknown_fields_such_as_user(self):
        tx = self.create()
        with self.assertRaises(s.ValidationFailed):
            s.update_transaction(self.a, tx.id, user=self.b)

    def test_update_and_delete(self):
        tx = self.create()
        tx = s.update_transaction(self.a, tx.id, amount="10.00", note="lunch")
        self.assertEqual((tx.amount, tx.note), (D("10.00"), "lunch"))
        s.delete_transaction(self.a, tx.id)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_other_user_cannot_touch_my_transaction(self):
        tx = self.create()
        with self.assertRaises(s.NotFound):
            s.update_transaction(self.b, tx.id, amount="1.00")
        with self.assertRaises(s.NotFound):
            s.delete_transaction(self.b, tx.id)
        with self.assertRaises(s.NotFound):
            s.delete_transaction(self.a, "not-a-uuid")
        self.assertEqual(Transaction.objects.get(id=tx.id).amount, D("125.50"))


class CategoryAndBudgetServiceTests(TestCase):
    def setUp(self):
        self.a, self.b, self.c = make_world()

    def test_duplicate_category_is_a_conflict_and_does_not_break_the_session(self):
        s.create_category(self.a, name="Snacks", kind="expense")
        with self.assertRaises(s.Conflict):
            s.create_category(self.a, name="snacks", kind="expense")
        s.create_category(self.a, name="Snacks", kind="income")          # still usable afterwards

    def test_cannot_archive_system_or_foreign_category(self):
        with self.assertRaises(s.NotFound):
            s.archive_category(self.a, self.c["food"].id)
        with self.assertRaises(s.NotFound):
            s.archive_category(self.a, self.c["b_private"].id)

    def test_budget_overlap_is_a_conflict_adjacent_is_fine(self):
        kw = dict(category_id=self.c["food"].id, period_type="monthly", limit_amount="500")
        s.create_budget(self.a, start_date="2026-10-01", end_date="2026-10-31", **kw)
        with self.assertRaises(s.Conflict):
            s.create_budget(self.a, start_date="2026-10-15", end_date="2026-11-15", **kw)
        s.create_budget(self.a, start_date="2026-11-01", end_date="2026-11-30", **kw)
        self.assertEqual(Budget.objects.count(), 2)

    def test_budget_validation(self):
        kw = dict(category_id=self.c["food"].id, period_type="monthly")
        with self.assertRaises(s.ValidationFailed):
            s.create_budget(self.a, start_date="2026-10-31", end_date="2026-10-01", limit_amount="1", **kw)
        with self.assertRaises(s.ValidationFailed):
            s.create_budget(self.a, start_date="2026-10-01", end_date="2026-10-31", limit_amount="0", **kw)
        with self.assertRaises(s.ValidationFailed):                       # budgets are for spending
            s.create_budget(self.a, category_id=self.c["salary"].id, period_type="monthly",
                            start_date="2026-10-01", end_date="2026-10-31", limit_amount="10")


class GoalServiceTests(TestCase):
    def setUp(self):
        self.a, self.b, self.c = make_world()
        self.goal = s.create_goal(self.a, name="Laptop", target_amount="1000")

    def add(self, amount, goal=None):
        return s.record_contribution(self.a, (goal or self.goal).id, amount=amount, contribution_date=D1)

    def test_contribution_updates_total_and_keeps_goal_active(self):
        _, goal, total = self.add("400")
        self.assertEqual((total, goal.status), (D("400.00"), "active"))

    def test_reaching_target_completes_goal(self):
        self.add("400")
        _, goal, total = self.add("600")
        self.assertEqual((total, goal.status), (D("1000.00"), "completed"))
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, "completed")

    def test_overshoot_is_allowed_once_then_goal_is_closed(self):
        _, goal, total = self.add("1500")
        self.assertEqual((total, goal.status), (D("1500.00"), "completed"))
        with self.assertRaises(s.Conflict):
            self.add("1")

    def test_paused_and_archived_goals_reject_money(self):
        s.change_goal_status(self.a, self.goal.id, "paused")
        with self.assertRaises(s.Conflict):
            self.add("10")
        self.assertEqual(GoalContribution.objects.count(), 0)

    def test_other_user_cannot_contribute_or_change_my_goal(self):
        with self.assertRaises(s.NotFound):
            s.record_contribution(self.b, self.goal.id, amount="10", contribution_date=D1)
        with self.assertRaises(s.NotFound):
            s.change_goal_status(self.b, self.goal.id, "archived")

    def test_invalid_contribution_amounts(self):
        for bad in ("0", "-1", 0.5, "1.999"):
            with self.subTest(bad=bad), self.assertRaises(s.ValidationFailed):
                self.add(bad)

    def test_deleting_contribution_reopens_goal_that_is_no_longer_funded(self):
        c1, _, _ = self.add("600")
        c2, goal, _ = self.add("400")
        self.assertEqual(goal.status, "completed")
        goal, total = s.delete_contribution(self.a, self.goal.id, c2.id)
        self.assertEqual((total, goal.status), (D("600.00"), "active"))

    def test_cannot_delete_a_contribution_through_the_wrong_goal(self):
        other = s.create_goal(self.a, name="Trip", target_amount="500")
        c1, _, _ = self.add("100")
        with self.assertRaises(s.NotFound):
            s.delete_contribution(self.a, other.id, c1.id)
        self.assertEqual(GoalContribution.objects.count(), 1)

    def test_status_transitions(self):
        g = self.goal.id
        s.change_goal_status(self.a, g, "paused")
        with self.assertRaises(s.Conflict):
            s.change_goal_status(self.a, g, "completed")                 # paused -> completed not allowed
        s.change_goal_status(self.a, g, "active")
        s.change_goal_status(self.a, g, "archived")
        with self.assertRaises(s.Conflict):
            s.change_goal_status(self.a, g, "paused")                    # archived -> only active
        with self.assertRaises(s.ValidationFailed):
            s.change_goal_status(self.a, g, "bogus")

    def test_cannot_reopen_a_fully_funded_goal(self):
        self.add("1000")
        with self.assertRaises(s.Conflict):
            s.change_goal_status(self.a, self.goal.id, "active")

    # ---- atomicity: all-or-nothing -------------------------------------- #
    def test_failure_while_completing_rolls_back_the_contribution(self):
        self.add("400")
        with mock.patch.object(SavingsGoal, "save", side_effect=RuntimeError("disk full")):
            with self.assertRaises(RuntimeError):
                self.add("600")                                           # would complete the goal
        self.assertEqual(GoalContribution.objects.count(), 1)            # the 600 was rolled back
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, "active")

    def test_create_goal_with_initial_contribution_is_all_or_nothing(self):
        goal = s.create_goal(self.a, name="Trip", target_amount="500", initial_contribution="100")
        self.assertEqual(_total(goal), D("100.00"))
        before = SavingsGoal.objects.count()
        with mock.patch.object(s, "record_contribution", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                s.create_goal(self.a, name="Car", target_amount="900", initial_contribution="50")
        self.assertEqual(SavingsGoal.objects.count(), before)            # the goal row was rolled back too


def _total(goal):
    return sum(c.amount for c in GoalContribution.objects.filter(goal=goal))


# --------------------------------------------------------------------------- #
# Concurrency: several PostgreSQL connections at once
# --------------------------------------------------------------------------- #
def run_in_threads(n, fn):
    """Run fn(i) in n threads released at the same instant. Returns the results
    (or the exceptions raised) in thread order."""
    barrier, results = threading.Barrier(n), [None] * n

    def worker(i):
        try:
            barrier.wait(timeout=10)
            results[i] = fn(i)
        except Exception as e:                       # collected for the assertions
            results[i] = e
        finally:
            connection.close()                       # each thread owns its own DB connection

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads: t.start()
    for t in threads: t.join(timeout=60)
    return results


class ConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.a, self.b, self.c = make_world()

    def test_simultaneous_contributions_never_lose_or_overshoot(self):
        """Target 100; 12 requests of 10 arrive at the same instant.
        With the row lock they run one after another: exactly 10 succeed, the goal
        completes exactly once, and the last 2 are refused because it is already complete."""
        goal = s.create_goal(self.a, name="Race", target_amount="100")
        results = run_in_threads(
            12, lambda i: s.record_contribution(self.a, goal.id, amount="10", contribution_date=D1))
        ok = [r for r in results if isinstance(r, tuple)]
        refused = [r for r in results if isinstance(r, s.Conflict)]
        crashed = [r for r in results if not isinstance(r, (tuple, s.Conflict))]
        self.assertEqual(crashed, [])
        self.assertEqual((len(ok), len(refused)), (10, 2))
        goal.refresh_from_db()
        self.assertEqual(_total(goal), D("100"))
        self.assertEqual(goal.status, "completed")

    def test_simultaneous_overlapping_budgets_only_one_wins(self):
        """The database's exclusion constraint decides, even when requests race."""
        results = run_in_threads(6, lambda i: s.create_budget(
            self.a, category_id=self.c["food"].id, period_type="monthly",
            start_date="2026-10-01", end_date="2026-10-31", limit_amount="500"))
        self.assertEqual(sum(isinstance(r, Budget) for r in results), 1)
        self.assertEqual(sum(isinstance(r, s.Conflict) for r in results), 5)
        self.assertEqual(Budget.objects.count(), 1)

    def test_simultaneous_edits_of_one_transaction_are_serialised(self):
        tx = s.create_transaction(self.a, category_id=self.c["food"].id, type="expense",
                                  amount="1.00", transaction_date="2026-10-01")
        results = run_in_threads(8, lambda i: s.update_transaction(self.a, tx.id, amount=f"{i + 1}.00"))
        self.assertTrue(all(isinstance(r, Transaction) for r in results), results)
        final = Transaction.objects.get(id=tx.id).amount
        self.assertIn(final, [D(f"{i + 1}.00") for i in range(8)])       # one whole edit, never a mixture
