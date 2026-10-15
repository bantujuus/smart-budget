from django.contrib import admin
from .models import Budget, Category, GoalContribution, SavingsGoal, Transaction, User

for m in (User, Category, Transaction, Budget, SavingsGoal, GoalContribution):
    admin.site.register(m)
