"""Administrator endpoints. Every view requires the admin role."""
from django.db.models import Q
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services_admin
from .admin_serializers import (
    AdminCategorySerializer,
    AdminUserFilterSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
)
from .finance_serializers import CategoryInputSerializer
from .models import Category, User
from .permissions import IsAdminRole


class AdminPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 200


class AdminStatsView(APIView):
    """GET /admin/stats/ - system-wide counts."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response(services_admin.system_stats())


class AdminUserListView(APIView):
    """GET /admin/users/?q=&is_active= - accounts (paginated)."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        filters = AdminUserFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        f = filters.validated_data
        qs = User.objects.order_by("-created_at")
        if "q" in f:
            qs = qs.filter(Q(email__icontains=f["q"]) | Q(full_name__icontains=f["q"]))
        if "is_active" in f:
            qs = qs.filter(is_active=f["is_active"])
        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(AdminUserSerializer(page, many=True).data)


class AdminUserDetailView(APIView):
    """PATCH /admin/users/{id}/ - activate or deactivate an account."""

    permission_classes = [IsAdminRole]

    def patch(self, request, pk):
        data = AdminUserUpdateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        user = services_admin.set_user_active(request.user, pk, data.validated_data["is_active"])
        return Response(AdminUserSerializer(user).data)


class AdminCategoryListCreateView(APIView):
    """GET/POST /admin/categories/ - the default categories every user sees."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        qs = Category.objects.filter(user__isnull=True).order_by("kind", "name")
        return Response(AdminCategorySerializer(qs, many=True).data)

    def post(self, request):
        data = CategoryInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        category = services_admin.create_system_category(request.user, **data.validated_data)
        return Response(AdminCategorySerializer(category).data, status=status.HTTP_201_CREATED)


class AdminCategoryDetailView(APIView):
    """DELETE /admin/categories/{id}/ - archive a default category."""

    permission_classes = [IsAdminRole]

    def delete(self, request, pk):
        services_admin.archive_system_category(request.user, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)