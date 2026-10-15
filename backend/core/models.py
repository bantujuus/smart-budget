"""
Smart Budgeting and Financial Goal Management System - data model.

Implements the ERD in docs/03_SmartBudget_System_Design_ERD.pdf:
User, Category, Transaction, Budget, SavingsGoal, GoalContribution.

Design decisions (the ERD lists these as "decision required"; change if the team decides otherwise):
  * Primary keys ........ UUID (not guessable in URLs).
  * Login identifier .... email (unique, case-insensitive).
  * Currency ............ single currency, ZMW, stored on the user.
  * Categories .......... system defaults (user IS NULL) + user's own categories.
  * Contributions ....... separate records, NOT transactions -> no double counting.
  * Deletion ............ categories/goals are archived; rows referenced by
                          money records cannot be hard-deleted (PROTECT).
  * Budget overlap ...... one budget per user+category cannot overlap in time
                          (PostgreSQL exclusion constraint).
"""
import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeOperators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.utils import timezone

MONEY = dict(max_digits=12, decimal_places=2)


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


# --------------------------------------------------------------------------- #
# User
# --------------------------------------------------------------------------- #
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, email, password, **extra):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)  # hashed by Django (PBKDF2 by default)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self._create(email, password, **extra)


class User(UUIDModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=254, unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    currency = models.CharField(max_length=3, default="ZMW")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        db_table = "users"
        constraints = [
            # case-insensitive uniqueness: Given@x.com == given@x.com
            models.UniqueConstraint(Lower("email"), name="uniq_user_email_ci"),
        ]

    def __str__(self):
        return self.email


# --------------------------------------------------------------------------- #
# Category
# --------------------------------------------------------------------------- #
class Category(UUIDModel):
    class Kind(models.TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"
        BOTH = "both", "Both"

    # NULL user  => system default category visible to everyone
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField(max_length=80)
    kind = models.CharField(max_length=7, choices=Kind.choices)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "categories"
        verbose_name_plural = "categories"
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=["income", "expense", "both"]), name="category_kind_valid"
            ),
            # unique per owner + kind, case-insensitive (per-user categories)
            models.UniqueConstraint(
                Lower("name"), "kind", "user",
                condition=Q(user__isnull=False), name="uniq_category_user_name_kind",
            ),
            # same rule for system defaults (user IS NULL, which UNIQUE would ignore)
            models.UniqueConstraint(
                Lower("name"), "kind",
                condition=Q(user__isnull=True), name="uniq_category_system_name_kind",
            ),
        ]
        indexes = [models.Index(fields=["user", "kind"], name="idx_category_user_kind")]

    def __str__(self):
        return f"{self.name} ({self.kind})"


# --------------------------------------------------------------------------- #
# Transaction
# --------------------------------------------------------------------------- #
class Transaction(UUIDModel):
    class Type(models.TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="transactions")
    type = models.CharField(max_length=7, choices=Type.choices)
    amount = models.DecimalField(**MONEY)
    transaction_date = models.DateField()
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "transactions"
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="transaction_amount_positive"),
            models.CheckConstraint(
                condition=Q(type__in=["income", "expense"]), name="transaction_type_valid"
            ),
        ]
        indexes = [
            models.Index(fields=["user", "-transaction_date"], name="idx_txn_user_date"),
            models.Index(fields=["user", "type", "transaction_date"], name="idx_txn_user_type_date"),
            models.Index(fields=["user", "category", "transaction_date"], name="idx_txn_user_cat_date"),
        ]

    def clean(self):
        # Category must be visible to the user and valid for the transaction type.
        c = self.category
        if c.user_id is not None and c.user_id != self.user_id:
            raise ValidationError({"category": "Category does not belong to this user."})
        if c.kind != "both" and c.kind != self.type:
            raise ValidationError({"category": f"A '{c.kind}' category cannot be used for {self.type}."})

    def __str__(self):
        return f"{self.type} {self.amount} on {self.transaction_date}"


# --------------------------------------------------------------------------- #
# Budget
# --------------------------------------------------------------------------- #
class Budget(UUIDModel):
    class Period(models.TextChoices):
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"
        CUSTOM = "custom", "Custom"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="budgets")
    period_type = models.CharField(max_length=7, choices=Period.choices, default=Period.MONTHLY)
    start_date = models.DateField()
    end_date = models.DateField()
    limit_amount = models.DecimalField(**MONEY)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "budgets"
        constraints = [
            models.CheckConstraint(condition=Q(limit_amount__gt=0), name="budget_limit_positive"),
            models.CheckConstraint(
                condition=Q(end_date__gte=F("start_date")), name="budget_end_not_before_start"
            ),
            models.CheckConstraint(
                condition=Q(period_type__in=["weekly", "monthly", "custom"]),
                name="budget_period_valid",
            ),
            # Duplicate-budget policy: no overlapping periods for the same user + category.
            # Range is inclusive on both ends ('[]').
            ExclusionConstraint(
                name="budget_no_overlap",
                expressions=[
                    ("user", RangeOperators.EQUAL),
                    ("category", RangeOperators.EQUAL),
                    (
                        models.Func(F("start_date"), F("end_date"), models.Value("[]"),
                                    function="daterange", output_field=DateRangeField()),
                        RangeOperators.OVERLAPS,
                    ),
                ],
            ),
        ]
        indexes = [models.Index(fields=["user", "start_date", "end_date"], name="idx_budget_user_period")]

    def clean(self):
        c = self.category
        if c.user_id is not None and c.user_id != self.user_id:
            raise ValidationError({"category": "Category does not belong to this user."})
        if c.kind == "income":
            raise ValidationError({"category": "Budgets apply to expense categories."})

    def __str__(self):
        return f"{self.category.name}: {self.limit_amount} ({self.start_date}..{self.end_date})"


# --------------------------------------------------------------------------- #
# SavingsGoal
# --------------------------------------------------------------------------- #
class SavingsGoal(UUIDModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        COMPLETED = "completed", "Completed"
        ARCHIVED = "archived", "Archived"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="goals")
    name = models.CharField(max_length=120)
    target_amount = models.DecimalField(**MONEY)
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=9, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "savings_goals"
        constraints = [
            models.CheckConstraint(condition=Q(target_amount__gt=0), name="goal_target_positive"),
            models.CheckConstraint(
                condition=Q(status__in=["active", "paused", "completed", "archived"]),
                name="goal_status_valid",
            ),
            # needed so goal_contributions can enforce "contribution owner == goal owner"
            models.UniqueConstraint(fields=["id", "user"], name="uniq_goal_id_user"),
        ]
        indexes = [models.Index(fields=["user", "status"], name="idx_goal_user_status")]

    def __str__(self):
        return self.name


# --------------------------------------------------------------------------- #
# GoalContribution
# --------------------------------------------------------------------------- #
class GoalContribution(UUIDModel):
    goal = models.ForeignKey(SavingsGoal, on_delete=models.CASCADE, related_name="contributions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contributions")
    amount = models.DecimalField(**MONEY)
    contribution_date = models.DateField()
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "goal_contributions"
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="contribution_amount_positive"),
        ]
        indexes = [
            models.Index(fields=["goal", "contribution_date"], name="idx_contrib_goal_date"),
            models.Index(fields=["user", "contribution_date"], name="idx_contrib_user_date"),
        ]

    def clean(self):
        if self.goal_id and self.goal.user_id != self.user_id:
            raise ValidationError({"goal": "Goal does not belong to this user."})

    def __str__(self):
        return f"{self.amount} -> {self.goal_id}"
