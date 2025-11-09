# Generated manually to fix varchar(10) constraint error

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('statements', '0013_alter_accountvalue_current_value'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE statements_statement ALTER COLUMN statement_type TYPE varchar(20);",
            reverse_sql="ALTER TABLE statements_statement ALTER COLUMN statement_type TYPE varchar(10);"
        ),
    ]
