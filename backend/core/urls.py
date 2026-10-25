from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    UserProfileView,
    CategoryListView,
    TransactionListCreateView,
    TransactionDetailView,
    BudgetListCreateView,
    BudgetDetailView,
    GoalListCreateView,
    GoalContributionView,
    DashboardTotalsView,
    CategorySummaryView,
    InsightsView,
)

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('me/', UserProfileView.as_view(), name='user-profile'),

    # Categories
    path('categories/', CategoryListView.as_view(), name='category-list'),

    # Transactions
    path('transactions/', TransactionListCreateView.as_view(), name='transaction-list-create'),
    path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),

    # Budgets
    path('budgets/', BudgetListCreateView.as_view(), name='budget-list-create'),
    path('budgets/<int:pk>/', BudgetDetailView.as_view(), name='budget-detail'),

    # Goals
    path('goals/', GoalListCreateView.as_view(), name='goal-list-create'),
    path('goals/<int:pk>/contributions/', GoalContributionView.as_view(), name='goal-contribution'),

    # Reports & Dashboard
    path('dashboard/', DashboardTotalsView.as_view(), name='dashboard-totals'),
    path('reports/summary/', CategorySummaryView.as_view(), name='category-summary'),
    path('insights/', InsightsView.as_view(), name='insights'),
]