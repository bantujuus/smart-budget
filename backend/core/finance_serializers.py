"""Serializers for categories and transactions.

Rule of thumb used here: serializers check the *shape* of what the client sent
(is the field there? is it text?), and core/services.py checks the *business rules*
(amount > 0, category matches type, ownership). Money is passed through untouched so
services.py can reject floating-point numbers.
"""
from rest_framework import serializers

from .models import Category, Transaction


# ----------------------------- output (what the API returns) ----------------------------- #
class CategorySerializer(serializers.ModelSerializer):
    is_system = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "kind", "is_system"]
        read_only_fields = fields

    def get_is_system(self, obj):
        return obj.user_id is None  # system default categories belong to nobody


class TransactionSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)  # nested, so the UI needs no second request

    class Meta:
        model = Transaction
        fields = ["id", "type", "amount", "transaction_date", "note", "category", "created_at"]
        read_only_fields = fields


# ----------------------------- input (what the client sends) ----------------------------- #
class CategoryInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=80)
    kind = serializers.CharField()


class TransactionInputSerializer(serializers.Serializer):
    """Used for POST (all fields required) and PATCH (partial=True: only what was sent)."""

    category_id = serializers.CharField()
    type = serializers.CharField()
    amount = serializers.JSONField()          # raw value: services.py rejects floats
    transaction_date = serializers.CharField()
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class TransactionFilterSerializer(serializers.Serializer):
    """Query string for GET /transactions/ (?type=&category=&start_date=&end_date=)."""

    type = serializers.ChoiceField(choices=["income", "expense"], required=False)
    category = serializers.UUIDField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    def validate(self, attrs):
        start, end = attrs.get("start_date"), attrs.get("end_date")
        if start and end and start > end:
            raise serializers.ValidationError({"start_date": ["Start date must not be after end date."]})
        return attrs