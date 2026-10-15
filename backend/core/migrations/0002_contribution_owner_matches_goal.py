from django.db import migrations


class Migration(migrations.Migration):
    """DB-level guarantee: a contribution's user_id must equal its goal's user_id."""

    dependencies = [("core", "0001_initial")]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE goal_contributions
              ADD CONSTRAINT fk_contribution_goal_same_owner
              FOREIGN KEY (goal_id, user_id) REFERENCES savings_goals (id, user_id)
              ON DELETE CASCADE;
            """,
            reverse_sql="ALTER TABLE goal_contributions DROP CONSTRAINT fk_contribution_goal_same_owner;",
        ),
    ]
