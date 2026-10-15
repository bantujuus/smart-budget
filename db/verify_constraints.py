import os, sys, datetime as dt
from decimal import Decimal as D
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")); os.environ["DJANGO_SETTINGS_MODULE"]="config.settings"
import django; django.setup()
from django.db import IntegrityError, transaction
from core.models import *

User.objects.filter(email__in=["a@test.zm","b@test.zm"]).delete()
a=User.objects.create_user("a@test.zm","pw-12345!x"); b=User.objects.create_user("b@test.zm","pw-12345!x")
food=Category.objects.get(user=None,name="Food"); sal=Category.objects.get(user=None,name="Salary")
d=dt.date(2026,10,1)
def expect_fail(label, fn):
    try:
        with transaction.atomic(): fn()
        print("FAIL (allowed):", label)
    except Exception as e:
        print("ok  blocked  :", label, "->", type(e).__name__)

Transaction.objects.create(user=a,category=food,type="expense",amount=D("125.50"),transaction_date=d)
expect_fail("zero amount", lambda: Transaction.objects.create(user=a,category=food,type="expense",amount=0,transaction_date=d))
expect_fail("negative amount", lambda: Transaction.objects.create(user=a,category=food,type="expense",amount=D("-5"),transaction_date=d))
expect_fail("duplicate email (case)", lambda: User.objects.create_user("A@TEST.zm","x"))
expect_fail("duplicate category", lambda: Category.objects.create(user=None,name="food",kind="expense"))
expect_fail("delete category in use", lambda: food.delete())
expect_fail("budget end<start", lambda: Budget.objects.create(user=a,category=food,start_date=d,end_date=d-dt.timedelta(1),limit_amount=100))
Budget.objects.create(user=a,category=food,period_type="monthly",start_date=dt.date(2026,10,1),end_date=dt.date(2026,10,31),limit_amount=500)
expect_fail("overlapping budget", lambda: Budget.objects.create(user=a,category=food,start_date=dt.date(2026,10,15),end_date=dt.date(2026,11,15),limit_amount=300))
Budget.objects.create(user=a,category=food,start_date=dt.date(2026,11,1),end_date=dt.date(2026,11,30),limit_amount=500); print("ok  allowed  : adjacent budget period")
g=SavingsGoal.objects.create(user=a,name="Laptop",target_amount=D("8000"))
GoalContribution.objects.create(goal=g,user=a,amount=D("250"),contribution_date=d); print("ok  allowed  : valid contribution")
expect_fail("contribution by other user to my goal", lambda: GoalContribution.objects.create(goal=g,user=b,amount=10,contribution_date=d))
expect_fail("zero contribution", lambda: GoalContribution.objects.create(goal=g,user=a,amount=0,contribution_date=d))
expect_fail("bad goal status", lambda: SavingsGoal.objects.create(user=a,name="x",target_amount=1,status="bogus"))
# model-level validation (app layer)
t=Transaction(user=a,category=sal,type="expense",amount=5,transaction_date=d)
try: t.clean(); print("FAIL type/kind mismatch allowed")
except Exception as e: print("ok  blocked  : income category on expense (clean())")
User.objects.filter(email__in=["a@test.zm","b@test.zm"]).delete()
print("cleanup done; leftover rows:", Transaction.objects.count(), Budget.objects.count(), SavingsGoal.objects.count())
