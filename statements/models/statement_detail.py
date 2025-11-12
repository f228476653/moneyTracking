from django.db import models
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
from .statement import Statement


class StatementDetail(models.Model):
    """Individual transaction details within a statement"""
    DIRECTION_CHOICES = [
        ('IN', 'In'),
        ('OUT', 'Out'),
    ]

    id = models.AutoField(primary_key=True)
    statement = models.ForeignKey(Statement, on_delete=models.CASCADE, related_name='statementdetail_set')
    item = models.CharField(max_length=255, db_index=True)
    transaction_date = models.DateField(db_index=True)
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    direction = models.CharField(max_length=6, choices=DIRECTION_CHOICES, db_index=True)

    class Meta:
        ordering = ['-transaction_date']
        verbose_name = 'Statement Detail'
        verbose_name_plural = 'Statement Details'
        indexes = [
            models.Index(fields=['statement', '-transaction_date']),
            models.Index(fields=['transaction_date', 'direction']),
            models.Index(fields=['direction', 'amount']),
        ]
    
    def __str__(self):
        return f"{self.item} - {self.amount} ({self.direction}) on {self.transaction_date}"


# Signal handlers to clear Statement cache when details change
@receiver(post_save, sender=StatementDetail)
@receiver(post_delete, sender=StatementDetail)
def clear_statement_cache(sender, instance, **kwargs):
    """Clear statement cache when details are modified"""
    if instance.statement_id:
        try:
            statement = Statement.objects.get(pk=instance.statement_id)
            statement.clear_cache()
        except Statement.DoesNotExist:
            pass
