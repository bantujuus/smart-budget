from django.urls import path

from . import admin_views, analytics_views, finance_views, planning_views, views

urlpatterns = [
    # authentication
    path("auth/csrf/", views.CsrfView.as_view(), name="auth-csrf"),
    path("auth/register/", views.RegisterView.as_view(), name="auth-register"),
    path("auth/login/", views.LoginView.as_view(), name="auth-login"),
    path("auth/logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("me/", views.MeView.as_view(), name="me"),
    # categories
    path("categories/", finance_views.CategoryListCreateView.as_view(), name="category-list"),
    path("categories/<str:pk>/", finance_views.CategoryDetailView.as_view(), name="category-detail"),
    # transactions
    path("transactions/", finance_views.TransactionListCreateView.as_view(), name="transaction-list"),
    path("transactions/<str:pk>/", finance_views.TransactionDetailView.as_view(), name="transaction-detail"),
    # budgets
    path("budgets/", planning_views.BudgetListCreateView.as_view(), name="budget-list"),
    path("budgets/<str:pk>/", planning_views.BudgetDetailView.as_view(), name="budget-detail"),
    # savings goals and contributions
    path("goals/", planning_views.GoalListCreateView.as_view(), name="goal-list"),
    path("goals/<str:pk>/", planning_views.GoalDetailView.as_view(), name="goal-detail"),
    path("goals/<str:pk>/contributions/", planning_views.ContributionListCreateView.as_view(),
         name="contribution-list"),
    path("goals/<str:pk>/contributions/<str:contribution_id>/",
         planning_views.ContributionDetailView.as_view(), name="contribution-detail"),
    # dashboard, reports, insights
    path("dashboard/", analytics_views.DashboardView.as_view(), name="dashboard"),
    path("reports/summary/", analytics_views.ReportSummaryView.as_view(), name="report-summary"),
    path("insights/", analytics_views.InsightsView.as_view(), name="insights"),
    # administrator (role: admin)
    path("admin/stats/", admin_views.AdminStatsView.as_view(), name="admin-stats"),
    path("admin/users/", admin_views.AdminUserListView.as_view(), name="admin-user-list"),
    path("admin/users/<str:pk>/", admin_views.AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("admin/categories/", admin_views.AdminCategoryListCreateView.as_view(), name="admin-category-list"),
    path("admin/categories/<str:pk>/", admin_views.AdminCategoryDetailView.as_view(), name="admin-category-detail"),
]