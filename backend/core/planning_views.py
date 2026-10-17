"""Budget and savings-goal endpoints (same pattern as finance_views.py)."""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import queries, services, services_budgets
from .planning_serializers import (
    BudgetFilterSerializer,
    BudgetInputSerializer,
    BudgetSerializer,
    BudgetUpdateSerializer,
    ContributionInputSerializer,
    ContributionSerializer,
    GoalFilterSerializer,
    GoalInputSerializer,
    GoalSerializer,
    GoalStatusSerializer,
)


# --------------------------------------------------------------------------- #
# Budgets
# --------------------------------------------------------------------------- #
def _budget_with_usage(user, budget_id):
    """One budget with its used/remaining figures (re-read after a write)."""
    for b in queries.budgets_with_usage(user):
        if str(b.id) == str(budget_id):
            return b
    raise services.NotFound("Budget not found.")


class BudgetListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filters = BudgetFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        f = filters.validated_data
        period = (f["start_date"], f["end_date"]) if "start_date" in f else None
        budgets = queries.budgets_with_usage(request.user, on_or_overlapping=period)
        return Response(BudgetSerializer(budgets, many=True).data)

    def post(self, request):
        data = BudgetInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        budget = services.create_budget(request.user, **data.validated_data)
        return Response(
            BudgetSerializer(_budget_with_usage(request.user, budget.id)).data,
            status=status.HTTP_201_CREATED,
        )


class BudgetDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        data = BudgetUpdateSerializer(data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        budget = services_budgets.update_budget(request.user, pk, **data.validated_data)
        return Response(BudgetSerializer(_budget_with_usage(request.user, budget.id)).data)

    def delete(self, request, pk):
        services_budgets.delete_budget(request.user, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------------------- #
# Savings goals
# --------------------------------------------------------------------------- #
def _goal_with_progress(user, goal_id):
    """One goal with its progress figures, or NotFound (also for someone else's goal)."""
    try:
        goal = queries.goals_with_progress(user).filter(id=goal_id).first()
    except (ValueError, DjangoValidationError):
        goal = None
    if goal is None:
        raise services.NotFound("Savings goal not found.")
    return goal


class GoalListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filters = GoalFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        goals = queries.goals_with_progress(request.user, status=filters.validated_data.get("status"))
        return Response(GoalSerializer(goals, many=True).data)

    def post(self, request):
        data = GoalInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        goal = services.create_goal(request.user, **data.validated_data)
        return Response(
            GoalSerializer(_goal_with_progress(request.user, goal.id)).data,
            status=status.HTTP_201_CREATED,
        )


class GoalDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response(GoalSerializer(_goal_with_progress(request.user, pk)).data)

    def patch(self, request, pk):
        """Only the status can be changed (pause, resume, complete, archive)."""
        data = GoalStatusSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        services.change_goal_status(request.user, pk, data.validated_data["status"])
        return Response(GoalSerializer(_goal_with_progress(request.user, pk)).data)


class ContributionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _goal_with_progress(request.user, pk)  # 404 unless the goal is the user's own
        contributions = queries.goal_contributions(request.user, pk)
        return Response(ContributionSerializer(contributions, many=True).data)

    def post(self, request, pk):
        data = ContributionInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        contribution, _goal, _total = services.record_contribution(
            request.user, pk, **data.validated_data
        )
        return Response(
            {
                "contribution": ContributionSerializer(contribution).data,
                "goal": GoalSerializer(_goal_with_progress(request.user, pk)).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ContributionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, contribution_id):
        services.delete_contribution(request.user, pk, contribution_id)
        return Response(status=status.HTTP_204_NO_CONTENT)