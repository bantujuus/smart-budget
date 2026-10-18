"""Dashboard, reports and insights endpoints (read-only)."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import insights, queries
from .analytics_serializers import PeriodSerializer, ReportQuerySerializer
from .finance_serializers import TransactionSerializer
from .planning_serializers import BudgetSerializer, GoalSerializer


def _period_block(start, end):
    return {"start_date": start, "end_date": end}


def _category_rows(rows):
    return [
        {"category_id": r["category_id"], "category": r["category__name"],
         "total": r["total"], "share_pct": r["share_pct"]}
        for r in rows
    ]


class DashboardView(APIView):
    """GET /dashboard/ - cards, budget status, goal progress and recent activity."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = PeriodSerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        start, end = q.period()
        user = request.user
        recent = queries.list_transactions(user, start=start, end=end)[:5]
        return Response({
            "period": _period_block(start, end),
            "currency": user.currency,
            "totals": queries.dashboard_totals(user, start, end),
            "budgets": BudgetSerializer(queries.budgets_with_usage(user, on_or_overlapping=(start, end)), many=True).data,
            "goals": GoalSerializer(queries.goals_with_progress(user, status="active"), many=True).data,
            "recent_transactions": TransactionSerializer(recent, many=True).data,
        })


class ReportSummaryView(APIView):
    """GET /reports/summary/ - totals, spending by category and the trend over time."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = ReportQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        start, end = q.period()
        granularity = q.validated_data["granularity"]
        user = request.user
        return Response({
            "period": _period_block(start, end),
            "currency": user.currency,
            "granularity": granularity,
            "totals": queries.dashboard_totals(user, start, end),
            "expense_by_category": _category_rows(queries.totals_by_category(user, start, end, "expense")),
            "income_by_category": _category_rows(queries.totals_by_category(user, start, end, "income")),
            "trend": queries.cash_flow_trend(user, start, end, granularity),
        })


class InsightsView(APIView):
    """GET /insights/ - explainable rule-based tips for the period."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = PeriodSerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        start, end = q.period()
        result = insights.build_insights(request.user, start, end)
        return Response({"period": _period_block(start, end), **result})