"""Serializers for the administrator endpoints."""
from rest_framework import serializers

from .models import Category, User
from .permissions import role_of


class StrictBooleanField(serializers.BooleanField):
    """A boolean that is treated as MISSING when it is not sent.

    DRF's normal BooleanField turns a missing value into False when the data comes from a
    form or a query string. For "is_active" that would mean an empty request silently
    deactivates an account, or that a missing filter means "only inactive users".
    """

    default_empty_html = serializers.empty


class AdminUserSerializer(serializers.ModelSerializer):
    """Account details an administrator may see. No password, and no financial data."""

    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role", "is_active", "created_at", "last_login"]
        read_only_fields = fields

    def get_role(self, obj):
        return role_of(obj)


class AdminUserUpdateSerializer(serializers.Serializer):
    is_active = StrictBooleanField()   # the ONLY thing an admin can change about an account


class AdminUserFilterSerializer(serializers.Serializer):
    q = serializers.CharField(required=False, max_length=100)    # search in email / name
    is_active = StrictBooleanField(required=False)


class AdminCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "kind", "is_archived", "created_at"]
        read_only_fields = fields