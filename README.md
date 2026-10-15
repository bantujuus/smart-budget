# Smart Budgeting and Financial Goal Management System

Stack (per docs/03 ERD, pending team confirmation): React + TypeScript, Django REST Framework, PostgreSQL.

```
smart-budget/
├── backend/    Django project (config/) + app (core/) with models and migrations
├── frontend/   React app goes here
├── db/         create_database.sql, schema.sql (reference), seed_categories.sql, verify_constraints.py
├── docs/       the 9 PDF documents from the documentation pack
├── .env.example
```

## Setup

1. Install Python 3.11+ and PostgreSQL 14+.
2. Create the database (edit the password first): `psql -U postgres -f db/create_database.sql`
3. `cp .env.example .env` and set `DB_PASSWORD` (and a real `DJANGO_SECRET_KEY`).
4. ```
   cd backend
   python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py seed_defaults
   python manage.py createsuperuser
   python manage.py runserver
   ```
5. Optional check that the database enforces its rules: `python db/verify_constraints.py` (uses and then deletes its own test rows).

**Migrations are the source of truth.** `db/schema.sql` is a reference dump; do not apply both.

## Tables

| Table | Purpose | Key rules |
|---|---|---|
| users | accounts (email login) | unique email (case-insensitive), hashed password, currency default ZMW |
| categories | income/expense labels | `user_id` NULL = system default; unique name per owner+kind; archived, not deleted |
| transactions | income & expense records | amount > 0, DECIMAL(12,2), category PROTECTed |
| budgets | category spending limit for a period | limit > 0, end >= start, **no overlapping periods** per user+category |
| savings_goals | goals | target > 0, status active/paused/completed/archived |
| goal_contributions | money put toward a goal | amount > 0, **owner must equal goal's owner** (composite FK) |

Contributions are separate from transactions, so saving is never double counted.

## Decisions I made (ERD marked them "decision required")

UUID primary keys · email login · single currency ZMW · default categories shared system-wide · budget periods weekly/monthly/custom with no overlap · archive rather than delete for categories/goals. Change them in `backend/core/models.py` and regenerate migrations if the team decides differently.

## Not enforced by the database

"Category kind must match transaction type" and "user can only use their own or system categories" are checked in model `clean()` (call it from the API serializers); they span tables, so a plain CHECK can't express them.
