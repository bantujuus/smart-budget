# ORM Queries

Module: `backend/core/queries.py` (read-only). Tests: `backend/core/tests.py`. Demo: `python manage.py demo_queries`.

## Rules every query follows

| Rule | Why | How it is enforced |
|---|---|---|
| First argument is always the authenticated `user` and every query filters on it | FR-14 data isolation | Tests give user B a large transaction and check user A never sees it |
| Inclusive date ranges (`start <= date <= end`) | Calculation contract in the API specification | Boundary-day tests |
| `Decimal` for all money, never `float` | NFR / ERD constraint | A test sums ten amounts of 0.10 and expects exactly 1.00 |
| Totals computed by the database | One round trip, no Python loops | `assertNumQueries` tests |
| Related rows joined, not fetched one at a time | No N+1 queries | `select_related` plus `assertNumQueries(1)` tests |

## Function reference

| Function | API use | Calculation (from the contract) | ORM technique |
|---|---|---|---|
| `list_transactions` | GET /transactions | filters: type, category, start, end | `filter`, `select_related`, `order_by` |
| `dashboard_totals` | GET /dashboard | income_total, expense_total, net_cash_flow = income - expense | one `aggregate` with conditional `Sum(filter=Q(...))` |
| `totals_by_category` | GET /reports/summary | spending per category with percentage share | `values().annotate(Sum)` |
| `cash_flow_trend` | GET /reports/summary | income, expense, net per day / week / month | `TruncMonth/Week/Day` + `values().annotate()` |
| `budgets_with_usage` | GET /budgets | budget_used, budget_remaining = limit - used (negative = overspent) | correlated `Subquery` with `OuterRef` |
| `overspent_budgets` | insights | budgets with remaining < 0 | built on `budgets_with_usage` |
| `goals_with_progress` | GET /goals | goal_contributed, goal_progress = contributed / target * 100, bar capped at 100 | `Sum` over the relation, `Round`, `Least`, `Greatest` |
| `goal_contributions` | GET /goals/{id}/contributions | contributions of one goal | filter on goal **and** user |
| `category_spend_vs_previous` | GET /insights | current vs previous equal-length period per category | two conditional `Sum`s in one query |

## Generated SQL (examples)

Dashboard totals, one query:

```sql
SELECT COALESCE(SUM(amount) FILTER (WHERE type = 'income'),  0.00) AS income_total,
       COALESCE(SUM(amount) FILTER (WHERE type = 'expense'), 0.00) AS expense_total
FROM transactions
WHERE transaction_date >= '2026-10-01' AND transaction_date <= '2026-10-31'
  AND user_id = '<current user>';
```

Budget usage: each budget gets `used` from a subquery that matches its own category and its own dates:

```sql
SELECT b.*, c.*,
       COALESCE((SELECT SUM(t.amount) FROM transactions t
                 WHERE t.category_id = b.category_id AND t.user_id = b.user_id
                   AND t.type = 'expense'
                   AND t.transaction_date BETWEEN b.start_date AND b.end_date
                 GROUP BY t.user_id), 0.00) AS used
FROM budgets b JOIN categories c ON c.id = b.category_id
WHERE b.user_id = '<current user>';
```

`remaining`, `used_pct` and `is_over` are then derived from `used` in Python, so the subquery runs once per budget rather than three times.

## Indexes that serve these queries

| Index | Serves |
|---|---|
| `idx_txn_user_date (user, -transaction_date)` | transaction list, date-range totals |
| `idx_txn_user_type_date (user, type, transaction_date)` | income/expense totals and trends |
| `idx_txn_user_cat_date (user, category, transaction_date)` | per-category totals and budget usage subquery |
| `idx_budget_user_period (user, start_date, end_date)` | budget period filters |
| `idx_contrib_goal_date (goal, contribution_date)` | goal contribution lists and sums |

## Testing

`python manage.py test core` runs 27 tests on a temporary PostgreSQL database. A deliberate bug (removing the owner filter, changing `<=` to `<`) makes 4 of them fail, which confirms they detect errors.

## Known limits

* Figures depend on manually entered records; net cash flow is not a verified bank balance.
* `cash_flow_trend` omits periods with no transactions; the frontend should treat a missing period as zero.
* `budgets_with_usage` returns a list rather than a QuerySet because it sets derived attributes in Python; a user has few budgets so this is fine.
