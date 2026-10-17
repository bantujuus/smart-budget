"""Category and transaction endpoints.

Every view follows the same pattern:
  1. check the request shape with a serializer,
  2. call a function in services.py / queries.py, passing request.user as the owner,
  3. return the result with a serializer.
The owner always comes from the session, never from the request body.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import queries, services
from .finance_serializers import (
    CategoryInputSerializer,
    CategorySerializer,
    TransactionFilterSerializer,
    TransactionInputSerializer,
    TransactionSerializer,
)
from .models import Category, Transaction


class TransactionPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 200


# --------------------------------------------------------------------------- #
# Categories
# --------------------------------------------------------------------------- #
class CategoryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """System defaults + the user's own categories (archived ones are hidden)."""
        qs = Category.objects.filter(
            Q(user=request.user) | Q(user__isnull=True), is_archived=False
        ).order_by("kind", "name")
        kind = request.query_params.get("kind")
        if kind in ("income", "expense"):
            qs = qs.filter(Q(kind=kind) | Q(kind="both"))
        return Response(CategorySerializer(qs, many=True).data)

    def post(self, request):
        data = CategoryInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        category = services.create_category(request.user, **data.validated_data)
        return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)


class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        """'Delete' = archive: old transactions keep their category, so history is never lost."""
        services.archive_category(request.user, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------------------- #
# Transactions
# --------------------------------------------------------------------------- #
def _owned_transaction(user, pk):
    """The user's own transaction, or NotFound (another user's id looks the same as a missing one)."""
    try:
        return Transaction.objects.select_related("category").get(id=pk, user=user)
    except (Transaction.DoesNotExist, ValueError, DjangoValidationError):
        raise services.NotFound("Transaction not found.")


class TransactionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filters = TransactionFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        f = filters.validated_data
        qs = queries.list_transactions(
            request.user,
            type=f.get("type"),
            category_id=f.get("category"),
            start=f.get("start_date"),
            end=f.get("end_date"),
        )
        paginator = TransactionPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(TransactionSerializer(page, many=True).data)

    def post(self, request):
        data = TransactionInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        tx = services.create_transaction(request.user, **data.validated_data)
        return Response(TransactionSerializer(tx).data, status=status.HTTP_201_CREATED)


class TransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response(TransactionSerializer(_owned_transaction(request.user, pk)).data)

    def patch(self, request, pk):
        data = TransactionInputSerializer(data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        tx = services.update_transaction(request.user, pk, **data.validated_data)
        return Response(TransactionSerializer(tx).data)

    def delete(self, request, pk):
        services.delete_transaction(request.user, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)