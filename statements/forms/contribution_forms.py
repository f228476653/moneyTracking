from django import forms
from django.contrib.auth.models import User
from ..models import ContributionRoom, Contribution
from decimal import Decimal


class ContributionRoomForm(forms.ModelForm):
    """Form for setting contribution room limits"""
    
    class Meta:
        model = ContributionRoom
        fields = ['user', 'account_type', 'limit', 'tax_year']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-control'
            }),
            'account_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'tax_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '2000',
                'max': '2100'
            }),
        }


class ContributionForm(forms.ModelForm):
    """Form for logging contributions"""
    
    class Meta:
        model = Contribution
        fields = ['user', 'account_type', 'amount', 'date', 'tax_year']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-control'
            }),
            'account_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tax_year': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        users = kwargs.pop('users', None)
        super().__init__(*args, **kwargs)
        
        if users:
            self.fields['user'].queryset = users
        else:
            self.fields['user'].queryset = User.objects.all()
        
        # Set default date to today
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['date'].initial = timezone.now().date()
        
        # Make tax_year only visible for RRSP in first 60 days
        self.fields['tax_year'].widget = forms.RadioSelect(
            choices=Contribution.TAX_YEAR_CHOICES,
            attrs={'class': 'form-check-input'}
        )
        self.fields['tax_year'].initial = 'current'

