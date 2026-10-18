"""Tests for role-based access control and the administrator endpoints."""
from rest_framework.test import APIClient

from core.models import Category, Transaction, User
from core.test_api_finance import PW, FinanceApiBase


class AdminBase(FinanceApiBase):
    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_user("admin@example.com", PW, is_staff=True)
        self.admin_client = self.browser_for(self.admin)


class RoleTests(AdminBase):
    def test_me_shows_the_role(self):
        self.assertEqual(self.client.get("/api/v1/me/").json()["role"], "user")
        self.assertEqual(self.admin_client.get("/api/v1/me/").json()["role"], "admin")

    def test_registering_with_is_staff_does_not_make_an_admin(self):
        c = APIClient(enforce_csrf_checks=True)
        c.get("/api/v1/auth/csrf/")
        r = c.post("/api/v1/auth/register/",
                   {"email": "sneaky@example.com", "password": PW, "is_staff": True, "is_superuser": True, "role": "admin"},
                   format="json", HTTP_X_CSRFTOKEN=c.cookies["csrftoken"].value)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["role"], "user")
        self.assertFalse(User.objects.get(email="sneaky@example.com").is_staff)

    def test_admin_has_no_extra_access_to_other_peoples_money(self):
        tx = self.make_tx()                                    # belongs to alice
        self.assertEqual(self.admin_client.get(f"/api/v1/transactions/{tx.id}/").status_code, 404)
        self.assertEqual(self.admin_client.get("/api/v1/transactions/").json()["count"], 0)


class AccessControlTests(AdminBase):
    ENDPOINTS = [
        ("get", "/api/v1/admin/stats/"),
        ("get", "/api/v1/admin/users/"),
        ("patch", "/api/v1/admin/users/{uid}/"),
        ("get", "/api/v1/admin/categories/"),
        ("post", "/api/v1/admin/categories/"),
        ("delete", "/api/v1/admin/categories/{cid}/"),
    ]

    def call(self, client, method, url):
        url = url.format(uid=self.bob.id, cid=self.food.id)
        body = {"is_active": False} if method == "patch" else {"name": "X", "kind": "expense"}
        return getattr(client, method)(url, body, format="json") if method in ("post", "patch") else getattr(client, method)(url)

    def test_normal_user_is_forbidden_everywhere(self):
        for method, url in self.ENDPOINTS:
            r = self.call(self.client, method, url)
            self.assertEqual(r.status_code, 403, f"{method} {url}")
            self.assertEqual(r.json()["error"]["code"], "PERMISSION_DENIED")

    def test_anonymous_is_refused_everywhere(self):
        anon = APIClient()
        for method, url in self.ENDPOINTS:
            self.assertIn(self.call(anon, method, url).status_code, (401, 403), f"{method} {url}")

    def test_forbidden_requests_change_nothing(self):
        self.call(self.client, "patch", "/api/v1/admin/users/{uid}/")
        self.call(self.client, "post", "/api/v1/admin/categories/")
        self.bob.refresh_from_db()
        self.assertTrue(self.bob.is_active)
        self.assertFalse(Category.objects.filter(name="X").exists())


class AdminStatsTests(AdminBase):
    def test_counts_only(self):
        self.make_tx()
        self.make_tx(user=self.bob)
        self.bob.is_active = False
        self.bob.save()
        r = self.admin_client.get("/api/v1/admin/stats/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["users"]["total"], 3)
        self.assertEqual(data["users"]["active"], 2)
        self.assertEqual(data["users"]["admins"], 1)
        self.assertEqual(data["users"]["new_last_30_days"], 3)
        self.assertEqual(data["records"]["transactions"], 2)
        self.assertEqual(data["categories"]["default"], 2)
        self.assertEqual(set(data["goals_by_status"]), {"active", "paused", "completed", "archived"})
        # privacy: no amounts, balances or e-mail addresses anywhere in the response
        text = r.content.decode()
        self.assertNotIn("10.00", text)
        self.assertNotIn("@", text)


class AdminUserTests(AdminBase):
    def test_list_has_no_secrets_and_can_filter(self):
        r = self.admin_client.get("/api/v1/admin/users/")
        self.assertEqual(r.json()["count"], 3)
        self.assertNotIn("password", r.content.decode())
        self.assertEqual(self.admin_client.get("/api/v1/admin/users/", {"q": "bob"}).json()["count"], 1)
        self.bob.is_active = False
        self.bob.save()
        inactive = self.admin_client.get("/api/v1/admin/users/", {"is_active": "false"}).json()
        self.assertEqual([u["email"] for u in inactive["results"]], ["bob@example.com"])

    def test_deactivated_user_cannot_log_in_and_loses_their_session(self):
        bob = self.browser_for(self.bob)
        self.assertEqual(bob.get("/api/v1/me/").status_code, 200)
        r = self.admin_client.patch(f"/api/v1/admin/users/{self.bob.id}/", {"is_active": False}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["is_active"])
        self.assertIn(bob.get("/api/v1/me/").status_code, (401, 403))           # existing session stops working
        fresh = APIClient(enforce_csrf_checks=True)
        fresh.get("/api/v1/auth/csrf/")
        login = fresh.post("/api/v1/auth/login/", {"email": "bob@example.com", "password": PW},
                           format="json", HTTP_X_CSRFTOKEN=fresh.cookies["csrftoken"].value)
        self.assertEqual(login.status_code, 400)

    def test_reactivate(self):
        self.admin_client.patch(f"/api/v1/admin/users/{self.bob.id}/", {"is_active": False}, format="json")
        self.admin_client.patch(f"/api/v1/admin/users/{self.bob.id}/", {"is_active": True}, format="json")
        self.bob.refresh_from_db()
        self.assertTrue(self.bob.is_active)

    def test_admin_cannot_deactivate_themselves(self):
        r = self.admin_client.patch(f"/api/v1/admin/users/{self.admin.id}/", {"is_active": False}, format="json")
        self.assertEqual(r.status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_the_only_field_an_admin_can_change_is_is_active(self):
        self.admin_client.patch(f"/api/v1/admin/users/{self.bob.id}/",
                                {"is_active": True, "is_staff": True, "email": "evil@example.com"}, format="json")
        self.bob.refresh_from_db()
        self.assertFalse(self.bob.is_staff)
        self.assertEqual(self.bob.email, "bob@example.com")

    def test_unknown_users(self):
        for pk in ("00000000-0000-0000-0000-000000000000", "not-a-uuid"):
            r = self.admin_client.patch(f"/api/v1/admin/users/{pk}/", {"is_active": False}, format="json")
            self.assertEqual(r.status_code, 404)

    def test_changes_are_audited(self):
        with self.assertLogs("smartbudget.audit", level="INFO") as logs:
            self.admin_client.patch(f"/api/v1/admin/users/{self.bob.id}/", {"is_active": False}, format="json")
        self.assertIn(str(self.admin.id), logs.output[0])
        self.assertIn("set_user_active", logs.output[0])


class AdminCategoryTests(AdminBase):
    def test_create_default_category_is_visible_to_everyone(self):
        r = self.admin_client.post("/api/v1/admin/categories/", {"name": "Airtime", "kind": "expense"}, format="json")
        self.assertEqual(r.status_code, 201)
        for who in (self.client, self.browser_for(self.bob)):
            cats = {c["name"]: c for c in who.get("/api/v1/categories/").json()}
            self.assertTrue(cats["Airtime"]["is_system"])

    def test_duplicate_and_invalid(self):
        self.assertEqual(self.admin_client.post("/api/v1/admin/categories/", {"name": "food", "kind": "expense"}, format="json").status_code, 409)
        self.assertEqual(self.admin_client.post("/api/v1/admin/categories/", {"name": "X", "kind": "weird"}, format="json").status_code, 400)
        self.assertEqual(self.admin_client.post("/api/v1/admin/categories/", {"name": "  ", "kind": "expense"}, format="json").status_code, 400)

    def test_archive_hides_it_but_keeps_history(self):
        tx = self.make_tx()                                    # uses the Food default category
        self.assertEqual(self.admin_client.delete(f"/api/v1/admin/categories/{self.food.id}/").status_code, 204)
        names = [c["name"] for c in self.client.get("/api/v1/categories/").json()]
        self.assertNotIn("Food", names)
        self.assertTrue(Transaction.objects.filter(id=tx.id, category=self.food).exists())
        listed = {c["name"]: c for c in self.admin_client.get("/api/v1/admin/categories/").json()}
        self.assertTrue(listed["Food"]["is_archived"])

    def test_admin_endpoint_cannot_archive_a_users_own_category(self):
        mine = Category.objects.create(user=self.alice, name="Church", kind="expense")
        self.assertEqual(self.admin_client.delete(f"/api/v1/admin/categories/{mine.id}/").status_code, 404)
        mine.refresh_from_db()
        self.assertFalse(mine.is_archived)

    def test_changes_are_audited(self):
        with self.assertLogs("smartbudget.audit", level="INFO") as logs:
            self.admin_client.post("/api/v1/admin/categories/", {"name": "Airtime", "kind": "expense"}, format="json")
        self.assertIn("create_default_category", logs.output[0])


class StrictBooleanTests(AdminBase):
    def test_empty_form_does_not_deactivate_an_account(self):
        r = self.admin_client.patch(f"/api/v1/admin/users/{self.bob.id}/", {}, format="multipart")
        self.assertEqual(r.status_code, 400)
        self.bob.refresh_from_db()
        self.assertTrue(self.bob.is_active)

    def test_missing_filter_means_no_filter(self):
        self.assertEqual(self.admin_client.get("/api/v1/admin/users/").json()["count"], 3)