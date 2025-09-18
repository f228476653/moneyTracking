from django import forms
from ..models import Account


class AddAccountForm(forms.ModelForm):
    """Form for adding new bank accounts"""
    
    class Meta:
        model = Account
        fields = ['bank_name', 'account_abbr', 'account_number', 'account_type']
        widgets = {
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter bank name (e.g., TD Bank, RBC, Amex)'
            }),
            'account_abbr': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter account abbreviation (e.g., CHK, SAV, CC)'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter account number (optional)'
            }),
            'account_type': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add help text
        self.fields['bank_name'].help_text = 'The name of the financial institution'
        self.fields['account_abbr'].help_text = 'Short abbreviation for the account (e.g., CHK for Chequing, SAV for Savings)'
        self.fields['account_number'].help_text = 'Account number (optional, for reference)'
        self.fields['account_type'].help_text = 'Type of account'
        
        # Make account_number optional
        self.fields['account_number'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        bank_name = cleaned_data.get('bank_name')
        account_abbr = cleaned_data.get('account_abbr')
        
        # Check if account with same abbreviation already exists
        if bank_name and account_abbr:
            existing_account = Account.objects.filter(
                bank_name=bank_name,
                account_abbr=account_abbr
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing_account.exists():
                raise forms.ValidationError(
                    f'An account with bank name "{bank_name}" and abbreviation "{account_abbr}" already exists.'
                )
        
        return cleaned_data
