# Database Transactions and Concurrency

Module: `backend/core/services.py` (all writes). Tests: `backend/core/test_services.py`.

## Why transactions

A budgeting system changes several rows that must stay consistent. Recording a goal contribution inserts a contribution **and** may change the goal's status. If only one of the two happened, the goal would show the wrong progress. A transaction makes the group all-or-nothing (the "A" in ACID).

## The three rules

| Rule | Mechanism | Where |
|---|---|---|
| All-or-nothing | `transaction.atomic()` around every multi-row write | `record_contribution`, `delete_contribution`, `create_goal`, `update_transaction`, `change_goal_status` |
| No lost updates | `select_for_update()` locks the row until the transaction commits | goal row (contributions, status changes), transaction row (edits) |
| Rules enforced by the database | constraints decide, services translate the error | `budget_no_overlap` exclusion constraint, CHECK constraints, composite foreign key |

## Function reference

| Function | Atomic block does | Failure it prevents |
|---|---|---|
| `create_transaction` | validate category, kind and amount, then insert | invalid or foreign-owner records |
| `update_transaction` | lock row, change fields, re-validate, save | two edits overwriting each other; type no longer matching category |
| `delete_transaction` | delete only the caller's row | deleting someone else's record |
| `create_category` / `archive_category` | insert (in a savepoint) / lock and flag | duplicate names; losing history (archived, never deleted) |
| `create_budget` | validate, insert, translate overlap error | overlapping budgets, even from simultaneous requests |
| `create_goal` | goal insert + optional first contribution | a goal without the contribution the user asked for (or the reverse) |
| `record_contribution` | lock goal, check active, insert, re-total, complete if funded | over-funding, double completion, lost total |
| `delete_contribution` | lock goal, delete, re-total, reopen if no longer funded | completed goals that are not actually funded |
| `change_goal_status` | lock goal, check allowed transition | illegal status changes |

## The race condition that the lock prevents

Goal target 100, current total 90, two requests each add 10 at the same moment.

Without a lock (both requests read the total before either commits):

| Step | Request A | Request B |
|---|---|---|
| 1 | reads status = active | reads status = active |
| 2 | inserts 10 | inserts 10 |
| 3 | total = 100, mark completed | total = 100, mark completed |

Both succeed, and in a bigger version of this the total drifts past the target, or the completion is applied twice or never. With the lock:

| Step | Request A | Request B |
|---|---|---|
| 1 | locks goal, status active | waits for the lock |
| 2 | inserts 10, total 100, completes, commits | |
| 3 | | gets the lock, reads status = **completed**, is refused |

PostgreSQL's default isolation level is READ COMMITTED: after B waits for the lock, its next query sees A's committed rows, so B's decision uses up-to-date data.

### Evidence

`ConcurrencyTests.test_simultaneous_contributions_never_lose_or_overshoot` starts 12 threads, each with its own PostgreSQL connection, released at the same instant, each adding 10 to a goal with target 100.

| Version | Result |
|---|---|
| With `select_for_update()` | exactly 10 succeed, 2 refused, total 100, goal completed (every run) |
| Lock removed (mutation test) | all 12 succeed, total 120, target overshot (failed 3 of 3 runs) |

Two more concurrency tests: six simultaneous identical budgets leave exactly one row (the exclusion constraint decides), and eight simultaneous edits of one transaction leave one whole edit, never a mixture.

## Deadlock avoidance

Each operation locks **one** row (the goal or the transaction being edited) and never waits for a second lock. Two requests therefore can never wait on each other in a circle. If a future feature must lock several goals, lock them in a fixed order (for example by `id`).

## Savepoints

Catching a database error inside a transaction normally leaves it unusable. Where a service expects a failure (duplicate category, overlapping budget) the insert runs in a nested `transaction.atomic()`, which is a savepoint: only that insert is undone and the surrounding transaction can carry on.

## Error contract for the API team

Every failure is a `ServiceError` with `code`, `message`, `fields` and a suggested `http_status`, matching the error format in the API specification:

| Exception | code | HTTP |
|---|---|---|
| `ValidationFailed` | VALIDATION_ERROR | 400 |
| `NotFound` (also used for another user's id) | NOT_FOUND | 404 |
| `Conflict` (overlap, goal not active, illegal status change) | CONFLICT | 409 |

```python
from core import services
from core.services import ServiceError

try:
    contribution, goal, total = services.record_contribution(
        request.user, goal_id, amount=request.data["amount"], contribution_date=request.data["date"])
except ServiceError as e:
    return Response(e.as_dict(), status=e.http_status)
```

Always pass `request.user`. Never pass a user id from the request body.

## Decisions made (change if the team decides otherwise)

* A contribution that pushes a goal over its target is accepted once; the goal then completes and refuses more money until reopened.
* Reaching the target completes the goal automatically.
* Deleting a contribution reopens a completed goal that is no longer fully funded.
* Goal status changes: active to paused, completed or archived; paused to active or archived; completed to active or archived; archived to active. A fully funded goal cannot be reopened without raising its target.
* Categories and goals are archived, not deleted; categories used by records cannot be hard-deleted.

## Known limits

* Locks are held only for the duration of one request, so the lock queue is short, but a very busy goal would serialise its contributions. For a personal budgeting system this is the correct trade-off.
* Money amounts must be strings, integers or `Decimal`. JSON numbers such as `0.1` arrive as floats and are rejected on purpose; the frontend must send `"0.10"`.
