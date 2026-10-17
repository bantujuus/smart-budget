"""Tests for register / login / logout / me."""
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import User

STRONG = "Tr0ub4dor&3-horse"


class AuthApiTests(TestCase):
    def setUp(self):
        cache.clear()  # the login throttle counts requests in the cache
        self.client = APIClient(enforce_csrf_checks=True)  # behave like a real browser

    def csrf(self):
        self.client.get("/api/v1/auth/csrf/")
        return {"HTTP_X_CSRFTOKEN": self.client.cookies["csrftoken"].value}

    def register(self, email="chris@example.com", password=STRONG, **extra):
        return self.client.post(
            "/api/v1/auth/register/",
            {"email": email, "password": password, **extra},
            format="json", **self.csrf(),
        )

    def test_register_creates_user_and_signs_in(self):
        r = self.register(full_name="Chris")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["email"], "chris@example.com")
        self.assertNotIn("password", r.data)
        self.assertEqual(self.client.get("/api/v1/me/").status_code, 200)

    def test_password_is_hashed(self):
        self.register()
        self.assertNotEqual(User.objects.get().password, STRONG)

    def test_duplicate_email_ignoring_case_is_rejected(self):
        self.register()
        r = self.register(email="CHRIS@example.com")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("email", r.data["error"]["fields"])

    def test_weak_password_is_rejected(self):
        r = self.register(password="12345678")
        self.assertEqual(r.status_code, 400)
        self.assertIn("password", r.data["error"]["fields"])

    def test_register_without_csrf_token_is_blocked(self):
        r = self.client.post(
            "/api/v1/auth/register/", {"email": "a@example.com", "password": STRONG}, format="json"
        )
        self.assertEqual(r.status_code, 403)

    def test_login_success(self):
        User.objects.create_user("chris@example.com", STRONG)
        r = self.client.post(
            "/api/v1/auth/login/", {"email": "Chris@Example.com", "password": STRONG},
            format="json", **self.csrf(),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/me/").data["email"], "chris@example.com")

    def test_login_failure_message_is_the_same_for_both_cases(self):
        User.objects.create_user("chris@example.com", STRONG)
        wrong_pw = self.client.post(
            "/api/v1/auth/login/", {"email": "chris@example.com", "password": "nope-nope-1"},
            format="json", **self.csrf())
        no_user = self.client.post(
            "/api/v1/auth/login/", {"email": "ghost@example.com", "password": "nope-nope-1"},
            format="json", **self.csrf())
        self.assertEqual(wrong_pw.status_code, 400)
        self.assertEqual(wrong_pw.data, no_user.data)

    def test_inactive_user_cannot_log_in(self):
        User.objects.create_user("chris@example.com", STRONG, is_active=False)
        r = self.client.post(
            "/api/v1/auth/login/", {"email": "chris@example.com", "password": STRONG},
            format="json", **self.csrf())
        self.assertEqual(r.status_code, 400)

    def test_login_is_throttled(self):
        for _ in range(10):
            self.client.post("/api/v1/auth/login/", {"email": "a@example.com", "password": "x"},
                             format="json", **self.csrf())
        r = self.client.post("/api/v1/auth/login/", {"email": "a@example.com", "password": "x"},
                             format="json", **self.csrf())
        self.assertEqual(r.status_code, 429)

    def test_me_requires_login(self):
        r = self.client.get("/api/v1/me/")
        self.assertIn(r.status_code, (401, 403))
        self.assertIn("error", r.data)

    def test_logout_ends_session(self):
        self.register()
        r = self.client.post("/api/v1/auth/logout/", **self.csrf())
        self.assertEqual(r.status_code, 204)
        self.assertIn(self.client.get("/api/v1/me/").status_code, (401, 403))