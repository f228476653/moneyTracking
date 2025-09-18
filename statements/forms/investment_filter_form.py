from django import forms
from ..models import Account


class InvestmentFilterForm(forms.Form):
    """Form for filtering investment data"""
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Filter investments created from this date'
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Filter investments created until this date'
    )
    
    account_filter = forms.ModelChoiceField(
        queryset=Account.objects.filter(account_type='INVESTMENT'),
        required=False,
        empty_label="All Investment Accounts",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Filter by specific investment account'
    )
