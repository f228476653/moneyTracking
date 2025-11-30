from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class ContributionRoom(models.Model):
    """Model to store contribution room limits for TFSA and RRSP per user"""
    
    ACCOUNT_TYPES = [
        ('TFSA', 'TFSA'),
        ('RRSP', 'RRSP'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='contribution_rooms',
        help_text='User this room belongs to'
    )
    account_type = models.CharField(
        max_length=10, 
        choices=ACCOUNT_TYPES,
        help_text='Type of registered account'
    )
    limit = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00'),
        help_text='Contribution room limit for this account type'
    )
    tax_year = models.IntegerField(
        help_text='Tax year this limit applies to (e.g., 2025)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user', 'tax_year', 'account_type']
        verbose_name = 'Contribution Room'
        verbose_name_plural = 'Contribution Rooms'
        unique_together = [['user', 'account_type', 'tax_year']]
    
    def __str__(self):
        return f"{self.user.username} - {self.account_type} ({self.tax_year}): ${self.limit}"


class Contribution(models.Model):
    """Model to track individual contributions to TFSA or RRSP accounts"""
    
    ACCOUNT_TYPES = [
        ('TFSA', 'TFSA'),
        ('RRSP', 'RRSP'),
    ]
    
    TAX_YEAR_CHOICES = [
        ('current', 'Current Year'),
        ('previous', 'Previous Year'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='contributions',
        help_text='User who made this contribution'
    )
    account_type = models.CharField(
        max_length=10, 
        choices=ACCOUNT_TYPES,
        help_text='Type of registered account'
    )
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Contribution amount'
    )
    date = models.DateField(help_text='Date of contribution')
    tax_year = models.CharField(
        max_length=10,
        choices=TAX_YEAR_CHOICES,
        default='current',
        help_text='Tax year this contribution applies to (for RRSP first 60 days)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Contribution'
        verbose_name_plural = 'Contributions'
    
    def __str__(self):
        return f"{self.user.username} - {self.account_type}: ${self.amount} ({self.date})"
