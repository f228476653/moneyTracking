from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from .account import Account


class AccountValue(models.Model):
    """Model to store current values of accounts"""
    
    id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='account_values')
    current_value = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        null=True,
        blank=True,
        help_text='Current value/balance of the account'
    )
    booking_value = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        null=True,
        blank=True,
        help_text='Booking value for investment accounts (original cost basis)'
    )
    date_updated = models.DateTimeField(auto_now=True, help_text='When this value was last updated')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_updated']
        verbose_name = 'Account Value'
        verbose_name_plural = 'Account Values'
        unique_together = ['account', 'date_updated']  # One value per account per day
    
    def __str__(self):
        return f"{self.account.bank_name} - {self.account.account_abbr}: ${self.current_value} ({self.date_updated.date()})"
