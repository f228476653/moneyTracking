from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from .account import Account


class InvestmentData(models.Model):
    """Investment data model for storing book cost and market value"""
    
    id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='investment_data')
    book_cost = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='The original cost basis of the investment'
    )
    market_value = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='The current market value of the investment'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Investment Data'
        verbose_name_plural = 'Investment Data'
    
    def __str__(self):
        return f"{self.account.bank_name} - {self.account.account_abbr}: Book Cost: {self.book_cost}, Market Value: {self.market_value}"
    
    @property
    def gain_loss(self):
        """Calculate the gain or loss"""
        return self.market_value - self.book_cost
    
    @property
    def gain_loss_percentage(self):
        """Calculate the gain or loss percentage"""
        if self.book_cost == 0:
            return Decimal('0.00')
        return (self.gain_loss / self.book_cost) * 100
