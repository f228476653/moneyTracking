# Generated manually

from django.db import migrations, models
from django.utils import timezone


def populate_date_field(apps, schema_editor):
    """Populate the date field from date_updated for existing records"""
    AccountValue = apps.get_model('statements', 'AccountValue')
    for account_value in AccountValue.objects.all():
        if account_value.date_updated:
            account_value.date = account_value.date_updated.date()
        else:
            account_value.date = timezone.now().date()
        account_value.save()


class Migration(migrations.Migration):

    dependencies = [
        ('statements', '0015_add_indexes_and_caching'),
    ]

    operations = [
        # First, remove the old unique_together constraint on account and date_updated
        migrations.AlterUniqueTogether(
            name='accountvalue',
            unique_together=set(),
        ),
        # Add the date field as nullable
        migrations.AddField(
            model_name='accountvalue',
            name='date',
            field=models.DateField(null=True, blank=True, help_text='Date for this account value (prevents duplicates per day)'),
        ),
        # Populate the date field from date_updated
        migrations.RunPython(populate_date_field, migrations.RunPython.noop),
        # Make the date field required
        migrations.AlterField(
            model_name='accountvalue',
            name='date',
            field=models.DateField(help_text='Date for this account value (prevents duplicates per day)'),
        ),
        # Add new unique_together constraint on account and date
        migrations.AlterUniqueTogether(
            name='accountvalue',
            unique_together={('account', 'date')},
        ),
    ]

