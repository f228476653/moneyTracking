from django import forms
from ..models import Account


class ReportFilterForm(forms.Form):
    """Form for filtering reports"""
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    bank_filter = forms.ModelChoiceField(
        queryset=Account.objects.values_list('bank_name', flat=True).distinct(),
        required=False,
        empty_label="All Banks",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    account_filter = forms.ModelChoiceField(
        queryset=Account.objects.all(),
        required=False,
        empty_label="All Accounts",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
