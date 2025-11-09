from django.db import models
from decimal import Decimal
from .account import Account


class Statement(models.Model):
    """Bank statement model"""
    STATEMENT_TYPES = [
        ('CSV', 'CSV'),
        ('EXCEL', 'Excel'),
        ('PDF', 'PDF'),
        ('TXT', 'Text'),
        ('OTHER', 'Other'),
    ]
    
    id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='statements')
    source_file = models.CharField(max_length=255, null=True, blank=True)
    statement_from_date = models.DateField()
    statement_to_date = models.DateField()
    statement_type = models.CharField(max_length=20, choices=STATEMENT_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-statement_to_date']
        verbose_name = 'Bank Statement'
        verbose_name_plural = 'Bank Statements'
    
    def __str__(self):
        return f"{self.account.bank_name} - {self.account.account_abbr} ({self.statement_from_date} to {self.statement_to_date})"
    
    @property
    def total_credits(self):
        return self.statementdetail_set.filter(direction='IN').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
    
    @property
    def total_debits(self):
        return self.statementdetail_set.filter(direction='OUT').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
    
    @property
    def total_in(self):
        return self.total_credits
    
    @property
    def total_out(self):
        return self.total_debits
    
    @property
    def net_amount(self):
        return self.total_credits - self.total_debits
