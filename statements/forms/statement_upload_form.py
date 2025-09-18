from django import forms
from django.core.validators import FileExtensionValidator
from ..models import Statement, Account


class StatementUploadForm(forms.ModelForm):
    """Form for uploading bank statements"""
    
    # Account selection dropdown
    account = forms.ModelChoiceField(
        queryset=Account.objects.all(),
        required=True,
        empty_label="-- Select Account --",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'account_dropdown'
        }),
        help_text='Select an existing account for this statement.'
    )
    
    # Investment fields (shown only for investment accounts)
    book_cost = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Enter book cost'
        }),
        help_text='The original cost basis of the investment'
    )
    
    market_value = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Enter market value'
        }),
        help_text='The current market value of the investment'
    )
    
    # Explicitly define source_file as FileField
    source_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        help_text='Upload your bank statement CSV file. The system will attempt to auto-detect bank name, account details, and dates from the file.'
    )
    
    class Meta:
        model = Statement
        fields = ['statement_from_date', 'statement_to_date']
        widgets = {
            'statement_from_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'statement_to_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Date fields will be conditionally required in clean() method
        for field_name in ['statement_from_date', 'statement_to_date']:
            self.fields[field_name].required = False
        
        # Add help text
        self.fields['statement_from_date'].help_text = (
            'Start date of the statement period (required for bank statements).'
        )
        self.fields['statement_to_date'].help_text = (
            'End date of the statement period (required for bank statements).'
        )
    
    def clean_source_file(self):
        file = self.cleaned_data.get('source_file')
        
        # Check if this is an investment account
        account = self.cleaned_data.get('account')
        
        is_investment_account = False
        if account and account.account_type == 'INVESTMENT':
            is_investment_account = True
        
        # For investment accounts, file is not required
        if is_investment_account:
            return None
        
        # For non-investment accounts, file is required
        if not file:
            raise forms.ValidationError('File upload is required for non-investment accounts.')
        
        # Check file size (max 10MB)
        if file.size > 10 * 1024 * 1024:
            raise forms.ValidationError('File size must be under 10MB.')
        
        # Check file extension - only CSV
        if not file.name.lower().endswith('.csv'):
            raise forms.ValidationError('Only CSV files are supported.')
        
        # Return the filename for storage
        return file.name
    
    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('statement_from_date')
        to_date = cleaned_data.get('statement_to_date')
        account = cleaned_data.get('account')
        
        # Check if this is an investment account
        is_investment_account = False
        if account and account.account_type == 'INVESTMENT':
            is_investment_account = True
        
        # For non-investment accounts, date fields are required
        if not is_investment_account:
            if not from_date:
                self.add_error('statement_from_date', 'This field is required for bank statements.')
            if not to_date:
                self.add_error('statement_to_date', 'This field is required for bank statements.')
        
        # Validate date range if both dates are provided
        if from_date and to_date and from_date > to_date:
            raise forms.ValidationError(
                'Statement start date cannot be after end date.'
            )
        
        # Check for overlapping date periods for the same account
        if not is_investment_account and from_date and to_date and account:
            overlapping_statements = Statement.objects.filter(
                account=account
            ).exclude(
                id=self.instance.id if self.instance else None
            ).filter(
                # Check if the new period overlaps with any existing period
                statement_from_date__lte=to_date,
                statement_to_date__gte=from_date
            )
            
            if overlapping_statements.exists():
                overlapping_statement = overlapping_statements.first()
                raise forms.ValidationError(
                    f'This statement period overlaps with an existing statement for the same account. '
                    f'Existing statement period: {overlapping_statement.statement_from_date} to {overlapping_statement.statement_to_date}. '
                    f'Please choose a different date range or update the existing statement.'
                )
        
        # For investment accounts, validate investment fields
        book_cost = cleaned_data.get('book_cost')
        market_value = cleaned_data.get('market_value')
        
        if is_investment_account:
            if not book_cost or not market_value:
                raise forms.ValidationError(
                    'For investment accounts, both book cost and market value are required.'
                )
        
        return cleaned_data
