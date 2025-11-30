# Generated manually to fix varchar(10) constraint error

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statements', '0013_alter_accountvalue_current_value'),
    ]

    operations = [
        migrations.AlterField(
            model_name='statement',
            name='statement_type',
            field=models.CharField(max_length=20),
        ),
    ]
