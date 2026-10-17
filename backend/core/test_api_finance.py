"""Tests for the category and transaction endpoints."""
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Category, Transaction, User

PW = "Tr0ub4dor&3-horse"


class FinanceApiBase(TestCase):
    def setUp(self):
        cache.clear()
        self.food = Category.objects.create(user=None, name="Food", kind="expense")
        self.salary = Category.objects.create(user=None, name="Salary", kind="income")
        self.alice = User.objects.create_user("alice@example.com", PW)
        self.bob = User.objects.create_user("bob@example.com", PW)
        self.client = self.browser_for(self.alice)

    def browser_for(self, user):
        """A client that behaves like a signed-in browser (CSRF checks switched on)."""
        c = APIClient(enforce_csrf_checks=True)
        c.get("/api/v1/auth/csrf/")
        c.force_login(user)
        c.defaults["HTTP_X_CSRFTOKEN"] = c.cookies["csrftoken"].value
        return c

    def make_tx(self, user=None, **kw):
        values = dict(user=user or self.alice, category=self.food, type="expense",
                      amount="10.00", transaction_date="2026-10-05")
        values.update(kw)
        return Transaction.objects.create(**values)

    def payload(self, **kw):
        base = {"category_id": str(self.food.id), "type": "expense",
                "amount": "125.50", "transaction_date": "2026-10-08", "note": "Groceries"}
        base.update(kw)
        return base


class CategoryApiTests(FinanceApiBase):
    def test_list_shows_defaults_and_own_but_not_other_users(self):
        Category.objects.create(user=self.alice, name="Church", kind="expense")
        Category.objects.create(user=self.bob, name="Secret", kind="expense")
        names = [c["name"] for c in self.client.get("/api/v1/categories/").data]
        self.assertIn("Food", names)
        self.assertIn("Church", names)
        self.assertNotIn("Secret", names)

    def test_create_category(self):
        r = self.client.post("/api/v1/categories/", {"name": "Church", "kind": "expense"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertFalse(r.data["is_system"])

    def test_duplicate_category_is_a_conflict(self):
        body = {"name": "Church", "kind": "expense"}
        self.client.post("/api/v1/categories/", body, format="json")
        r = self.client.post("/api/v1/categories/", {"name": "church", "kind": "expense"}, format="json")
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.data["error"]["code"], "CONFLICT")

    def test_delete_archives_own_category(self):
        mine = Category.objects.create(user=self.alice, name="Church", kind="expense")
        self.assertEqual(self.client.delete(f"/api/v1/categories/{mine.id}/").status_code, 204)
        mine.refresh_from_db()
        self.assertTrue(mine.is_archived)
        self.assertNotIn("Church", [c["name"] for c in self.client.get("/api/v1/categories/").data])

    def test_cannot_archive_system_or_other_users_category(self):
        theirs = Category.objects.create(user=self.bob, name="Secret", kind="expense")
        self.assertEqual(self.client.delete(f"/api/v1/categories/{self.food.id}/").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/v1/categories/{theirs.id}/").status_code, 404)

    def test_requires_login(self):
        self.assertIn(APIClient().get("/api/v1/categories/").status_code, (401, 403))


class TransactionApiTests(FinanceApiBase):
    def test_create_transaction(self):
        r = self.client.post("/api/v1/transactions/", self.payload(), format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["amount"], "125.50")          # money is returned as a string
        self.assertEqual(r.data["category"]["name"], "Food")

    def test_owner_comes_from_session_not_request(self):
        r = self.client.post("/api/v1/transactions/", self.payload(user=str(self.bob.id)), format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Transaction.objects.get(id=r.data["id"]).user, self.alice)

    def test_bad_amounts_are_rejected(self):
        for bad in ("0", "-5", "12.345", "abc", 12.5):
            r = self.client.post("/api/v1/transactions/", self.payload(amount=bad), format="json")
            self.assertEqual(r.status_code, 400, bad)
            self.assertIn("amount", r.data["error"]["fields"])

    def test_missing_fields_are_reported(self):
        r = self.client.post("/api/v1/transactions/", {"type": "expense"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("amount", r.data["error"]["fields"])

    def test_category_must_match_type(self):
        r = self.client.post("/api/v1/transactions/", self.payload(category_id=str(self.salary.id)), format="json")
        self.assertEqual(r.status_code, 400)

    def test_cannot_use_another_users_category(self):
        theirs = Category.objects.create(user=self.bob, name="Secret", kind="expense")
        r = self.client.post("/api/v1/transactions/", self.payload(category_id=str(theirs.id)), format="json")
        self.assertEqual(r.status_code, 404)

    def test_list_only_returns_own_transactions(self):
        self.make_tx()
        self.make_tx(user=self.bob)
        r = self.client.get("/api/v1/transactions/")
        self.assertEqual(r.data["count"], 1)

    def test_list_filters(self):
        self.make_tx(transaction_date="2026-10-01")
        self.make_tx(transaction_date="2026-10-20")
        self.make_tx(type="income", category=self.salary, transaction_date="2026-10-10")
        url = "/api/v1/transactions/"
        self.assertEqual(self.client.get(url, {"type": "income"}).data["count"], 1)
        self.assertEqual(self.client.get(url, {"start_date": "2026-10-05", "end_date": "2026-10-31"}).data["count"], 2)
        self.assertEqual(self.client.get(url, {"category": str(self.food.id)}).data["count"], 2)

    def test_start_after_end_is_rejected(self):
        r = self.client.get("/api/v1/transactions/", {"start_date": "2026-10-31", "end_date": "2026-10-01"})
        self.assertEqual(r.status_code, 400)

    def test_pagination_shape(self):
        for _ in range(3):
            self.make_tx()
        r = self.client.get("/api/v1/transactions/", {"limit": 2})
        self.assertEqual(r.data["count"], 3)
        self.assertEqual(len(r.data["results"]), 2)
        self.assertIsNotNone(r.data["next"])

    def test_detail_is_owner_scoped(self):
        mine, theirs = self.make_tx(), self.make_tx(user=self.bob)
        self.assertEqual(self.client.get(f"/api/v1/transactions/{mine.id}/").status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/transactions/{theirs.id}/").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/transactions/not-a-uuid/").status_code, 404)

    def test_patch_updates_only_sent_fields(self):
        tx = self.make_tx(note="old")
        r = self.client.patch(f"/api/v1/transactions/{tx.id}/", {"amount": "99.00"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["amount"], "99.00")
        self.assertEqual(r.data["note"], "old")

    def test_cannot_patch_or_delete_another_users_transaction(self):
        theirs = self.make_tx(user=self.bob)
        self.assertEqual(self.client.patch(f"/api/v1/transactions/{theirs.id}/", {"amount": "1.00"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/v1/transactions/{theirs.id}/").status_code, 404)
        self.assertTrue(Transaction.objects.filter(id=theirs.id).exists())

    def test_delete(self):
        tx = self.make_tx()
        self.assertEqual(self.client.delete(f"/api/v1/transactions/{tx.id}/").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/v1/transactions/{tx.id}/").status_code, 404)

    def test_requires_login(self):
        self.assertIn(APIClient().get("/api/v1/transactions/").status_code, (401, 403))

    def test_write_without_csrf_token_is_blocked(self):
        c = APIClient(enforce_csrf_checks=True)
        c.force_login(self.alice)   # signed in, but no CSRF header
        self.assertEqual(c.post("/api/v1/transactions/", self.payload(), format="json").status_code, 403)