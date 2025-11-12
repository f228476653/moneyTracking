from django.db import models
from django.core.cache import cache
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
    statement_from_date = models.DateField(db_index=True)
    statement_to_date = models.DateField(db_index=True)
    statement_type = models.CharField(max_length=20, choices=STATEMENT_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-statement_to_date']
        verbose_name = 'Bank Statement'
        verbose_name_plural = 'Bank Statements'
        indexes = [
            models.Index(fields=['account', '-statement_to_date']),
            models.Index(fields=['-uploaded_at']),
            models.Index(fields=['statement_from_date', 'statement_to_date']),
        ]
    
    def __str__(self):
        return f"{self.account.bank_name} - {self.account.account_abbr} ({self.statement_from_date} to {self.statement_to_date})"
    
    def _get_cache_key(self, suffix):
        """Generate cache key for this statement"""
        return f'statement_{self.id}_{suffix}'

    @property
    def total_credits(self):
        """Total credits with caching"""
        cache_key = self._get_cache_key('total_credits')
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            return cached_value

        total = self.statementdetail_set.filter(direction='IN').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        cache.set(cache_key, total, 3600)  # Cache for 1 hour
        return total

    @property
    def total_debits(self):
        """Total debits with caching"""
        cache_key = self._get_cache_key('total_debits')
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            return cached_value

        total = self.statementdetail_set.filter(direction='OUT').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        cache.set(cache_key, total, 3600)  # Cache for 1 hour
        return total

    @property
    def total_in(self):
        """Alias for total_credits"""
        return self.total_credits

    @property
    def total_out(self):
        """Alias for total_debits"""
        return self.total_debits

    @property
    def net_amount(self):
        """Net amount with caching"""
        cache_key = self._get_cache_key('net_amount')
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            return cached_value

        net = self.total_credits - self.total_debits
        cache.set(cache_key, net, 3600)  # Cache for 1 hour
        return net

    def clear_cache(self):
        """Clear cached totals for this statement"""
        cache.delete_many([
            self._get_cache_key('total_credits'),
            self._get_cache_key('total_debits'),
            self._get_cache_key('net_amount'),
        ])
