from django.urls import path

from . import finance_views, views

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
]