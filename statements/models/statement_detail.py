from django.db import models
from django.core.validators import MinValueValidator
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
    item = models.CharField(max_length=255)
    transaction_date = models.DateField()
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    direction = models.CharField(max_length=6, choices=DIRECTION_CHOICES)
    
    class Meta:
        ordering = ['-transaction_date']
        verbose_name = 'Statement Detail'
        verbose_name_plural = 'Statement Details'
    
    def __str__(self):
        return f"{self.item} - {self.amount} ({self.direction}) on {self.transaction_date}"
