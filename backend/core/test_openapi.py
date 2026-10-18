"""The OpenAPI 3.1 document must be valid, complete and consistent with the real routes."""
import re
import tempfile
from pathlib import Path

import yaml
from django.core.management import call_command
from django.test import TestCase
from django.urls import get_resolver
from rest_framework.test import APIClient


class OpenApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.spec = APIClient().get("/api/v1/schema/", {"format": "json"}).json()

    def test_is_a_valid_openapi_3_1_document_with_no_warnings(self):
        out = Path(tempfile.mkdtemp()) / "openapi.yaml"
        call_command("spectacular", "--fail-on-warn", "--validate", "--file", str(out))
        self.assertEqual(yaml.safe_load(out.read_text())["openapi"], "3.1.0")

    def test_version_and_title(self):
        self.assertEqual(self.spec["openapi"], "3.1.0")
        self.assertIn("Smart Budgeting", self.spec["info"]["title"])

    def test_every_route_is_documented(self):
        routes = set()
        for top in get_resolver().url_patterns:
            if str(top.pattern) != "api/v1/":
                continue
            for p in top.url_patterns:
                route = str(p.pattern)
                if route.startswith(("schema", "docs")):
                    continue
                route = re.sub(r"<str:pk>", "{id}", route)
                route = re.sub(r"<str:(\w+)>", r"{\1}", route)
                routes.add("/api/v1/" + route)
        self.assertTrue(routes)
        self.assertEqual(routes, set(self.spec["paths"]), "the spec and the URL list disagree")

    def test_every_operation_has_a_tag_a_summary_and_error_responses(self):
        for path, item in self.spec["paths"].items():
            for method, op in item.items():
                where = f"{method.upper()} {path}"
                self.assertTrue(op.get("tags"), where)
                self.assertTrue(op.get("summary"), where)
                if path != "/api/v1/auth/csrf/":
                    self.assertTrue({"400", "403", "404"} & set(op["responses"]), where)

    def test_state_changing_requests_document_the_csrf_header(self):
        for path, item in self.spec["paths"].items():
            for method in ("post", "patch", "delete"):
                if method in item:
                    names = [p["name"] for p in item[method].get("parameters", [])]
                    self.assertIn("X-CSRFToken", names, f"{method.upper()} {path}")

    def test_money_is_never_a_json_number(self):
        def walk(node, where):
            if isinstance(node, dict):
                self.assertNotEqual(node.get("type"), "number", where)
                for k, v in node.items():
                    walk(v, f"{where}/{k}")
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, f"{where}[{i}]")
        walk(self.spec["components"]["schemas"], "components")

    def test_swagger_page_is_served(self):
        r = APIClient().get("/api/v1/docs/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("swagger", r.content.decode().lower())