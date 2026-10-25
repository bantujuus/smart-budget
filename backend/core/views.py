from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model, authenticate
from rest_framework.authtoken.models import Token
from django.db.models import Sum, F
from datetime import datetime

from .models import Transaction, Category, Budget, SavingsGoal, GoalContribution

User = get_user_model()

# --- Authentication Views ---

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        full_name = request.data.get('full_name', '')

        if not email or not password:
            return Response({'detail': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'detail': 'An account with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create user using your custom UserManager (supports email-based auth)
        user = User.objects.create_user(email=email, password=password, full_name=full_name)
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': {
                'id': str(user.id),
                'email': user.email,
                'full_name': user.full_name,
                'currency': user.currency
            }
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Log what the frontend actually sent to the backend terminal for debugging
        print("LOGIN REQUEST DATA:", request.data)

        identifier = (
            request.data.get('email') or 
            request.data.get('username') or 
            request.data.get('identifier')
        )
        password = request.data.get('password')

        if not identifier or not password:
            return Response({'detail': 'Email and password fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_obj = User.objects.get(email=identifier)
        except User.DoesNotExist:
            return Response({'detail': f'User "{identifier}" not found.'}, status=status.HTTP_401_UNAUTHORIZED)

        user = authenticate(request, username=user_obj.email, password=password)

        if not user:
            return Response({'detail': 'Invalid password.'}, status=status.HTTP_401_UNAUTHORIZED)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': {
                'id': str(user.id),
                'email': user.email,
                'full_name': getattr(user, 'full_name', ''),
                'currency': getattr(user, 'currency', 'ZMW')
            }
        })

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': str(user.id),
            'email': user.email,
            'full_name': user.full_name,
            'currency': user.currency
        })

# --- Category View ---

class CategoryListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Check if Category model has a user field, otherwise return all
            if hasattr(Category, 'user'):
                categories = Category.objects.filter(user=request.user)
            else:
                categories = Category.objects.all()
            
            data = [{
                'id': str(cat.id) if hasattr(cat, 'id') else None,
                'name': getattr(cat, 'name', str(cat)),
                'type': getattr(cat, 'type', 'expense'),
            } for cat in categories]
            
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            name = request.data.get('name')
            cat_type = request.data.get('type', 'expense')
            
            if not name:
                return Response({'detail': 'Category name is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
            kwargs = {'name': name, 'type': cat_type}
            if hasattr(Category, 'user'):
                kwargs['user'] = request.user
                
            category = Category.objects.create(**kwargs)
            return Response({
                'id': str(category.id),
                'name': category.name,
                'type': getattr(category, 'type', 'expense')
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Transaction Views ---

class TransactionListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        txns = Transaction.objects.filter(user=request.user).order_by('-transaction_date')
        
        txn_type = request.query_params.get('type')
        category_id = request.query_params.get('category_id')
        if txn_type:
            txns = txns.filter(type=txn_type)
        if category_id:
            txns = txns.filter(category_id=category_id)

        data = [{
            'id': str(t.id),
            'amount': str(t.amount),
            'type': t.type,
            'category': {'id': str(t.category.id), 'name': t.category.name, 'kind': t.category.kind} if t.category else None,
            'transaction_date': str(t.transaction_date),
            'note': t.note
        } for t in txns]
        return Response(data)

    def post(self, request):
        data = request.data
        try:
            category = Category.objects.get(id=data.get('category_id'))
            txn = Transaction(
                user=request.user,
                amount=data.get('amount'),
                type=data.get('type', category.kind),
                category=category,
                transaction_date=data.get('transaction_date', datetime.today().date()),
                note=data.get('note', '')
            )
            txn.full_clean()  # Triggers model clean methods
            txn.save()
            return Response({
                'id': str(txn.id),
                'amount': str(txn.amount),
                'type': txn.type,
                'category': {'id': str(category.id), 'name': category.name},
                'transaction_date': str(txn.transaction_date),
                'note': txn.note
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class TransactionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            txn = Transaction.objects.get(pk=pk, user=request.user)
            data = request.data
            if 'amount' in data: txn.amount = data['amount']
            if 'note' in data: txn.note = data['note']
            if 'transaction_date' in data: txn.transaction_date = data['transaction_date']
            txn.full_clean()
            txn.save()
            return Response({'id': str(txn.id), 'amount': str(txn.amount), 'note': txn.note})
        except Transaction.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            txn = Transaction.objects.get(pk=pk, user=request.user)
            txn.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Transaction.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

# --- Budget Views ---

class BudgetListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        budgets = Budget.objects.filter(user=request.user)
        result = []
        for b in budgets:
            spent = Transaction.objects.filter(
                user=request.user,
                category=b.category,
                transaction_date__range=[b.start_date, b.end_date]
            ).aggregate(total=Sum('amount'))['total'] or 0.00
            
            limit = float(b.limit_amount)
            used_pct = round((float(spent) / limit) * 100, 1) if limit > 0 else 0
            
            result.append({
                'id': str(b.id),
                'category': {'id': str(b.category.id), 'name': b.category.name},
                'limit_amount': str(b.limit_amount),
                'start_date': str(b.start_date),
                'end_date': str(b.end_date),
                'used': str(spent),
                'remaining': str(limit - float(spent)),
                'used_pct': used_pct,
                'is_over': float(spent) > limit
            })
        return Response(result)

    def post(self, request):
        data = request.data
        try:
            category = Category.objects.get(id=data.get('category_id'))
            budget = Budget(
                user=request.user,
                category=category,
                limit_amount=data.get('limit_amount'),
                start_date=data.get('start_date'),
                end_date=data.get('end_date'),
                period_type=data.get('period_type', 'monthly')
            )
            budget.full_clean()
            budget.save()
            return Response({'id': str(budget.id), 'limit_amount': str(budget.limit_amount)}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BudgetDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            b = Budget.objects.get(pk=pk, user=request.user)
            b.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Budget.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)


# --- Savings Goal Views ---

class GoalListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        goals = SavingsGoal.objects.filter(user=request.user)
        result = []
        for g in goals:
            contributed = GoalContribution.objects.filter(goal=g).aggregate(total=Sum('amount'))['total'] or 0.00
            target = float(g.target_amount)
            progress = min(round((float(contributed) / target) * 100), 100) if target > 0 else 0
            
            result.append({
                'id': str(g.id),
                'name': g.name,
                'target_amount': str(g.target_amount),
                'target_date': str(g.target_date),
                'status': g.status,
                'goal_contributed': str(contributed),
                'goal_progress': progress
            })
        return Response(result)

    def post(self, request):
        data = request.data
        try:
            goal = SavingsGoal(
                user=request.user,
                name=data.get('name'),
                target_amount=data.get('target_amount'),
                target_date=data.get('target_date')
            )
            goal.full_clean()
            goal.save()
            return Response({'id': str(goal.id), 'name': goal.name}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GoalContributionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            goal = SavingsGoal.objects.get(pk=pk, user=request.user)
            data = request.data
            contrib = GoalContribution(
                goal=goal,
                user=request.user,
                amount=data.get('amount'),
                contribution_date=data.get('contribution_date', datetime.today().date()),
                note=data.get('note', '')
            )
            contrib.full_clean()
            contrib.save()
            return Response({'id': str(contrib.id), 'amount': str(contrib.amount)}, status=status.HTTP_201_CREATED)
        except SavingsGoal.DoesNotExist:
            return Response({'detail': 'Goal not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# --- Reports & Dashboard Views ---

class DashboardTotalsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        txns = Transaction.objects.filter(user=request.user)
        if start_date and end_date:
            txns = txns.filter(transaction_date__range=[start_date, end_date])

        income = txns.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0.00
        expense = txns.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0.00
        net = float(income) - float(expense)

        return Response({
            'income_total': f"{income:.2f}",
            'expense_total': f"{expense:.2f}",
            'net_cash_flow': f"{net:.2f}"
        })

class CategorySummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        txns = Transaction.objects.filter(user=request.user, type='expense')
        if start_date and end_date:
            txns = txns.filter(transaction_date__range=[start_date, end_date])

        total_expense = txns.aggregate(total=Sum('amount'))['total'] or 0.00
        summary = txns.values(cat_id=F('category__id'), cat_name=F('category__name')).annotate(total=Sum('amount'))

        result = []
        for item in summary:
            amt = float(item['total'] or 0)
            pct = round((amt / float(total_expense)) * 100, 1) if total_expense > 0 else 0
            result.append({
                'category_id': str(item['cat_id']),
                'category_name': item['cat_name'] or 'Uncategorized',
                'total_amount': f"{amt:.2f}",
                'percentage_share': pct
            })
        return Response(result)

class InsightsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        overspent_count = 0
        budgets = Budget.objects.filter(user=request.user)
        for b in budgets:
            spent = Transaction.objects.filter(user=request.user, category=b.category, transaction_date__range=[b.start_date, b.end_date]).aggregate(total=Sum('amount'))['total'] or 0
            if float(spent) > float(b.limit_amount):
                overspent_count += 1

        return Response({
            'category_changes': [],
            'overspent_count': overspent_count
        })