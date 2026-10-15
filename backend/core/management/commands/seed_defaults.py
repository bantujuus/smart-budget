"""Seed system-wide default categories (user = NULL). Safe to re-run."""
from django.core.management.base import BaseCommand
from core.models import Category

INCOME = ["Salary", "Allowance", "Business", "Gifts", "Other income"]
EXPENSE = ["Food", "Transport", "Rent", "Utilities", "Airtime & Data", "Education",
           "Health", "Entertainment", "Clothing", "Savings", "Other expense"]


class Command(BaseCommand):
    help = "Create default income/expense categories"

    def handle(self, *a, **kw):
        n = 0
        for kind, names in (("income", INCOME), ("expense", EXPENSE)):
            for name in names:
                _, created = Category.objects.get_or_create(user=None, name=name, kind=kind)
                n += created
        self.stdout.write(self.style.SUCCESS(f"{n} new default categories ({Category.objects.filter(user=None).count()} total)"))
