from django.db import models


class Account(models.Model):
    """Account model for storing account information"""
    ACCOUNT_TYPES = [
        ('CREDIT_CARD', 'Credit Card'),
        ('INVESTMENT', 'Investment'),
        ('BANK', 'Bank'),
    ]
    
    id = models.AutoField(primary_key=True)
    account_abbr = models.CharField(max_length=20, unique=True)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['bank_name', 'account_abbr']
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_abbr} ({self.get_account_type_display()})"
