"""Serializers for budgets, savings goals and contributions.

Same rule as finance_serializers.py: serializers check the shape of the request,
services check the business rules. Money fields use JSONField so the raw value reaches
services.py, which rejects floating-point numbers.
"""
from rest_framework import serializers

from .finance_serializers import CategorySerializer
from .models import Budget, GoalContribution, SavingsGoal


# ----------------------------- output ----------------------------- #
class BudgetSerializer(serializers.ModelSerializer):
    """Works with the objects from queries.budgets_with_usage (they carry the extra fields)."""

    category = CategorySerializer(read_only=True)
    used = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    remaining = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    used_pct = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    is_over = serializers.BooleanField(read_only=True)

    class Meta:
        model = Budget
        fields = ["id", "category", "period_type", "start_date", "end_date", "limit_amount",
                  "used", "remaining", "used_pct", "is_over"]
        read_only_fields = fields


class GoalSerializer(serializers.ModelSerializer):
    """Works with the objects from queries.goals_with_progress."""

    contributed = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    progress_pct = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    bar_pct = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    remaining_to_target = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = SavingsGoal
        fields = ["id", "name", "target_amount", "target_date", "status", "contributed",
                  "progress_pct", "bar_pct", "remaining_to_target", "created_at"]
        read_only_fields = fields


class ContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalContribution
        fields = ["id", "amount", "contribution_date", "note", "created_at"]
        read_only_fields = fields


# ----------------------------- input ----------------------------- #
class BudgetInputSerializer(serializers.Serializer):
    category_id = serializers.CharField()
    period_type = serializers.CharField()
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    limit_amount = serializers.JSONField()


class BudgetUpdateSerializer(serializers.Serializer):
    period_type = serializers.CharField(required=False)
    start_date = serializers.CharField(required=False)
    end_date = serializers.CharField(required=False)
    limit_amount = serializers.JSONField(required=False)


class BudgetFilterSerializer(serializers.Serializer):
    """?start_date=&end_date= : only budgets that overlap this period (both or neither)."""

    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    def validate(self, attrs):
        start, end = attrs.get("start_date"), attrs.get("end_date")
        if (start is None) != (end is None):
            raise serializers.ValidationError({"end_date": ["Send both start_date and end_date, or neither."]})
        if start and end and start > end:
            raise serializers.ValidationError({"start_date": ["Start date must not be after end date."]})
        return attrs


class GoalInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    target_amount = serializers.JSONField()
    target_date = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    initial_contribution = serializers.JSONField(required=False, allow_null=True)


class GoalStatusSerializer(serializers.Serializer):
    status = serializers.CharField()


class GoalFilterSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["active", "paused", "completed", "archived"], required=False)


class ContributionInputSerializer(serializers.Serializer):
    amount = serializers.JSONField()
    contribution_date = serializers.CharField()
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)