"""OpenAPI documentation for the API.

This file only DESCRIBES the endpoints (summary, request body, responses); it does not
change how any of them behave. It is imported by core/urls.py. Documentation lives here,
in one place, so the view files stay short and easy to read.
"""
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers as s

from . import admin_views, analytics_views, finance_views, planning_views, views
from .admin_serializers import (
    AdminCategorySerializer,
    AdminUserFilterSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
)
from .analytics_serializers import PeriodSerializer, ReportQuerySerializer
from .finance_serializers import (
    CategoryInputSerializer,
    CategorySerializer,
    TransactionFilterSerializer,
    TransactionInputSerializer,
    TransactionSerializer,
)
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
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

MONEY = dict(max_digits=14, decimal_places=2)


# ----------------------------- shared pieces ----------------------------- #
class ErrorBody(s.Serializer):
    code = s.CharField(help_text="Machine-readable code, e.g. VALIDATION_ERROR, NOT_FOUND, CONFLICT.")
    message = s.CharField()
    fields = s.DictField(child=s.ListField(child=s.CharField()), required=False,
                         help_text="Per-field messages (validation errors only).")


class ErrorResponse(s.Serializer):
    error = ErrorBody()


_ERR = {
    400: "Validation failed. See `error.fields`.",
    403: "Not signed in, missing or wrong CSRF token, or not allowed (wrong role).",
    404: "Not found. Other users' records also return 404, so ids cannot be probed.",
    409: "Conflicts with an existing record or a business rule.",
    429: "Too many attempts. Try again later.",
}


def err(*codes):
    return {c: OpenApiResponse(ErrorResponse, description=_ERR[c]) for c in codes}


def paged(name, item):
    return inline_serializer(name, {
        "count": s.IntegerField(),
        "next": s.URLField(allow_null=True),
        "previous": s.URLField(allow_null=True),
        "results": item(many=True),
    })


PAGE = [
    OpenApiParameter("limit", int, description="Page size (default 50, maximum 200)."),
    OpenApiParameter("offset", int, description="How many records to skip."),
]
ID = lambda what: OpenApiParameter("id", str, OpenApiParameter.PATH, description=f"{what} id (UUID).")  # noqa: E731

PeriodDoc = inline_serializer("Period", {"start_date": s.DateField(), "end_date": s.DateField()})
TotalsDoc = inline_serializer("Totals", {
    "income_total": s.DecimalField(**MONEY), "expense_total": s.DecimalField(**MONEY),
    "net_cash_flow": s.DecimalField(**MONEY)})
CategoryTotalDoc = inline_serializer("CategoryTotal", {
    "category_id": s.UUIDField(), "category": s.CharField(), "total": s.DecimalField(**MONEY),
    "share_pct": s.DecimalField(max_digits=8, decimal_places=1)})
TrendPointDoc = inline_serializer("TrendPoint", {
    "period": s.DateField(help_text="First day of the day/week/month."),
    "income": s.DecimalField(**MONEY), "expense": s.DecimalField(**MONEY), "net": s.DecimalField(**MONEY)})
InsightDoc = inline_serializer("Insight", {
    "rule": s.CharField(help_text="Which rule fired, e.g. BUDGET_OVER."),
    "severity": s.ChoiceField(["warning", "info", "positive"]),
    "title": s.CharField(), "message": s.CharField(),
    "explanation": s.CharField(help_text="Why this tip was shown (the rule and its threshold)."),
    "period": PeriodDoc, "data": s.DictField(help_text="The numbers behind the tip.")})


def many(doc):
    """A list of the documented object (inline_serializer returns an instance, not a class)."""
    return doc.__class__(many=True)


def tag(*, tags, **ops):
    """extend_schema_view(...) with the same tag on every operation."""
    return {name: extend_schema(tags=tags, **kw) for name, kw in ops.items()}


# ----------------------------- authentication ----------------------------- #
extend_schema_view(**tag(tags=["Authentication"], get=dict(
    summary="Get a CSRF cookie", auth=[],
    responses={200: inline_serializer("CsrfOk", {"detail": s.CharField()})},
)))(views.CsrfView)

extend_schema_view(**tag(tags=["Authentication"], post=dict(
    summary="Create an account and sign in", auth=[],
    request=RegisterSerializer, responses={201: UserSerializer, **err(400, 403, 429)},
)))(views.RegisterView)

extend_schema_view(**tag(tags=["Authentication"], post=dict(
    summary="Sign in", auth=[],
    description="Starts a session. A wrong email and a wrong password give the same message.",
    request=LoginSerializer, responses={200: UserSerializer, **err(400, 403, 429)},
)))(views.LoginView)

extend_schema_view(**tag(tags=["Authentication"], post=dict(
    summary="Sign out", request=None, responses={204: None, **err(403)},
)))(views.LogoutView)

extend_schema_view(**tag(tags=["Authentication"], get=dict(
    summary="Who am I?", description="The signed-in user, including their role (`user` or `admin`).",
    responses={200: UserSerializer, **err(403)},
)))(views.MeView)

# ----------------------------- categories ----------------------------- #
extend_schema_view(**tag(tags=["Categories"],
    get=dict(summary="List categories",
             description="Default categories plus the user's own (archived ones are hidden).",
             parameters=[OpenApiParameter("kind", str, enum=["income", "expense"],
                                          description="Only categories usable for this kind.")],
             responses={200: CategorySerializer(many=True), **err(403)}),
    post=dict(summary="Create a category", request=CategoryInputSerializer,
              responses={201: CategorySerializer, **err(400, 403, 409)}),
))(finance_views.CategoryListCreateView)

extend_schema_view(**tag(tags=["Categories"],
    delete=dict(summary="Archive a category", parameters=[ID("Category")],
                description="Hides it from new records; old transactions keep it.",
                responses={204: None, **err(403, 404)}),
))(finance_views.CategoryDetailView)

# ----------------------------- transactions ----------------------------- #
extend_schema_view(**tag(tags=["Transactions"],
    get=dict(summary="List transactions", operation_id="transactions_list", parameters=[TransactionFilterSerializer, *PAGE],
             responses={200: paged("PagedTransactions", TransactionSerializer), **err(400, 403)}),
    post=dict(summary="Record a transaction", request=TransactionInputSerializer,
              responses={201: TransactionSerializer, **err(400, 403, 404)}),
))(finance_views.TransactionListCreateView)

extend_schema_view(**tag(tags=["Transactions"],
    get=dict(summary="Get one transaction", parameters=[ID("Transaction")],
             responses={200: TransactionSerializer, **err(403, 404)}),
    patch=dict(summary="Edit a transaction", parameters=[ID("Transaction")],
               description="Send only the fields to change.", request=TransactionInputSerializer,
               responses={200: TransactionSerializer, **err(400, 403, 404)}),
    delete=dict(summary="Delete a transaction", parameters=[ID("Transaction")],
                responses={204: None, **err(403, 404)}),
))(finance_views.TransactionDetailView)

# ----------------------------- budgets ----------------------------- #
extend_schema_view(**tag(tags=["Budgets"],
    get=dict(summary="List budgets with usage",
             description="Each budget includes `used`, `remaining`, `used_pct` and `is_over`.",
             parameters=[BudgetFilterSerializer], responses={200: BudgetSerializer(many=True), **err(400, 403)}),
    post=dict(summary="Create a budget", description="One budget per category cannot overlap in time.",
              request=BudgetInputSerializer, responses={201: BudgetSerializer, **err(400, 403, 404, 409)}),
))(planning_views.BudgetListCreateView)

extend_schema_view(**tag(tags=["Budgets"],
    patch=dict(summary="Edit a budget", parameters=[ID("Budget")], request=BudgetUpdateSerializer,
               responses={200: BudgetSerializer, **err(400, 403, 404, 409)}),
    delete=dict(summary="Delete a budget", parameters=[ID("Budget")], responses={204: None, **err(403, 404)}),
))(planning_views.BudgetDetailView)

# ----------------------------- savings goals ----------------------------- #
extend_schema_view(**tag(tags=["Savings goals"],
    get=dict(summary="List savings goals with progress", parameters=[GoalFilterSerializer],
             responses={200: GoalSerializer(many=True), **err(400, 403)}),
    post=dict(summary="Create a savings goal", request=GoalInputSerializer,
              responses={201: GoalSerializer, **err(400, 403)}),
))(planning_views.GoalListCreateView)

extend_schema_view(**tag(tags=["Savings goals"],
    get=dict(summary="Get one goal", parameters=[ID("Goal")], responses={200: GoalSerializer, **err(403, 404)}),
    patch=dict(summary="Change a goal's status", parameters=[ID("Goal")],
               description="Pause, resume, complete or archive. Not every change is allowed (409).",
               request=GoalStatusSerializer, responses={200: GoalSerializer, **err(400, 403, 404, 409)}),
))(planning_views.GoalDetailView)

extend_schema_view(**tag(tags=["Savings goals"],
    get=dict(summary="List a goal's contributions", parameters=[ID("Goal")],
             responses={200: ContributionSerializer(many=True), **err(403, 404)}),
    post=dict(summary="Add money to a goal", parameters=[ID("Goal")], request=ContributionInputSerializer,
              description="Completes the goal automatically when the target is reached.",
              responses={201: inline_serializer("ContributionResult", {
                  "contribution": ContributionSerializer(), "goal": GoalSerializer()}),
                  **err(400, 403, 404, 409)}),
))(planning_views.ContributionListCreateView)

extend_schema_view(**tag(tags=["Savings goals"],
    delete=dict(summary="Remove a contribution", parameters=[ID("Goal"), OpenApiParameter(
        "contribution_id", str, OpenApiParameter.PATH, description="Contribution id (UUID).")],
        responses={204: None, **err(403, 404)}),
))(planning_views.ContributionDetailView)

# ----------------------------- dashboard and reports ----------------------------- #
extend_schema_view(**tag(tags=["Dashboard and reports"], get=dict(
    summary="Dashboard", description="Defaults to the current month when no dates are sent.",
    parameters=[PeriodSerializer],
    responses={200: inline_serializer("DashboardResponse", {
        "period": PeriodDoc, "currency": s.CharField(), "totals": TotalsDoc,
        "budgets": BudgetSerializer(many=True), "goals": GoalSerializer(many=True),
        "recent_transactions": TransactionSerializer(many=True)}), **err(400, 403)},
)))(analytics_views.DashboardView)

extend_schema_view(**tag(tags=["Dashboard and reports"], get=dict(
    summary="Report summary", parameters=[ReportQuerySerializer],
    responses={200: inline_serializer("ReportSummaryResponse", {
        "period": PeriodDoc, "currency": s.CharField(), "granularity": s.CharField(),
        "totals": TotalsDoc, "expense_by_category": many(CategoryTotalDoc),
        "income_by_category": many(CategoryTotalDoc), "trend": many(TrendPointDoc)}),
        **err(400, 403)},
)))(analytics_views.ReportSummaryView)

extend_schema_view(**tag(tags=["Dashboard and reports"], get=dict(
    summary="Smart insights",
    description="Explainable rule-based tips, most important first. Not financial advice.",
    parameters=[PeriodSerializer],
    responses={200: inline_serializer("InsightsResponse", {
        "period": PeriodDoc, "insights": many(InsightDoc), "message": s.CharField(),
        "disclaimer": s.CharField()}), **err(400, 403)},
)))(analytics_views.InsightsView)

# ----------------------------- administrator ----------------------------- #
extend_schema_view(**tag(tags=["Administrator"], get=dict(
    summary="System statistics", description="Counts only. Never amounts or personal details.",
    responses={200: inline_serializer("SystemStats", {
        "users": inline_serializer("UserCounts", {
            "total": s.IntegerField(), "active": s.IntegerField(), "admins": s.IntegerField(),
            "new_last_30_days": s.IntegerField()}),
        "records": inline_serializer("RecordCounts", {
            "transactions": s.IntegerField(), "budgets": s.IntegerField(), "goal_contributions": s.IntegerField()}),
        "goals_by_status": inline_serializer("GoalStatusCounts", {
            "active": s.IntegerField(), "paused": s.IntegerField(), "completed": s.IntegerField(),
            "archived": s.IntegerField()}),
        "categories": inline_serializer("CategoryCounts", {"default": s.IntegerField(), "custom": s.IntegerField()}),
        "generated_at": s.DateTimeField()}), **err(403)},
)))(admin_views.AdminStatsView)

extend_schema_view(**tag(tags=["Administrator"], get=dict(
    summary="List accounts", parameters=[AdminUserFilterSerializer, *PAGE],
    responses={200: paged("PagedAdminUsers", AdminUserSerializer), **err(400, 403)},
)))(admin_views.AdminUserListView)

extend_schema_view(**tag(tags=["Administrator"], patch=dict(
    summary="Activate or deactivate an account", parameters=[ID("User")],
    description="A deactivated user cannot sign in and loses any open session. Admins cannot deactivate themselves.",
    request=AdminUserUpdateSerializer, responses={200: AdminUserSerializer, **err(400, 403, 404)},
)))(admin_views.AdminUserDetailView)

extend_schema_view(**tag(tags=["Administrator"],
    get=dict(summary="List default categories", responses={200: AdminCategorySerializer(many=True), **err(403)}),
    post=dict(summary="Create a default category", request=CategoryInputSerializer,
              responses={201: AdminCategorySerializer, **err(400, 403, 409)}),
))(admin_views.AdminCategoryListCreateView)

extend_schema_view(**tag(tags=["Administrator"], delete=dict(
    summary="Archive a default category", parameters=[ID("Category")], responses={204: None, **err(403, 404)},
)))(admin_views.AdminCategoryDetailView)