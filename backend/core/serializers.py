"""Serializers for the authentication endpoints."""
from django.contrib.auth import authenticate, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """What the API shows about a user. Never includes the password."""

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "currency", "created_at"]
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")

    def validate_email(self, value):
        value = User.objects.normalize_email(value).strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs):
        # Run Django's password rules (length, common passwords, similarity to email, all digits).
        candidate = User(email=attrs["email"], full_name=attrs.get("full_name", ""))
        try:
            password_validation.validate_password(attrs["password"], candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    def create(self, validated_data):
        # create_user hashes the password; we never store it as plain text.
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    # Same message for "no such user" and "wrong password" so attackers can't tell which was wrong.
    GENERIC_ERROR = "Invalid email or password."

    def validate(self, attrs):
        # Emails are unique ignoring case, so find the account ignoring case too.
        found = User.objects.filter(email__iexact=attrs["email"].strip()).first()
        user = None
        if found is not None:
            user = authenticate(
                self.context.get("request"), username=found.email, password=attrs["password"]
            )
        if user is None:  # also None for deactivated accounts
            raise serializers.ValidationError(self.GENERIC_ERROR)
        attrs["user"] = user
        return attrs