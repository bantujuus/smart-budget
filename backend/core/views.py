"""Authentication API views (session + CSRF authentication)."""
from django.contrib.auth import login, logout
from django.db import IntegrityError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    """GET /auth/csrf/ - the frontend calls this first so the browser gets a CSRF cookie."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"detail": "CSRF cookie set."})


# DRF skips the CSRF check for anonymous users, but login/register must be protected too
# (otherwise another website could log a victim into the attacker's account), so we force it.
@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    """POST /auth/register/ - create an account and sign the user in."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.save()
        except IntegrityError:
            # Two people registering the same email at the same instant: the database wins.
            return Response(
                {"error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Please correct the highlighted fields.",
                    "fields": {"email": ["An account with this email already exists."]},
                }},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    """POST /auth/login/ - start a session."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"  # slows down password guessing

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)  # creates a fresh session id and rotates the CSRF token
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    """POST /auth/logout/ - end the session (CSRF is enforced by DRF for signed-in users)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """GET /me/ - the signed-in user's profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)