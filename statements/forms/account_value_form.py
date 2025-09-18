from django import forms


class AccountValueForm(forms.Form):
    """Form for updating current account values"""
    
    def __init__(self, *args, **kwargs):
        accounts = kwargs.pop('accounts', None)
        super().__init__(*args, **kwargs)
        
        if accounts:
            for account in accounts:
                # Market value field (current_value)
                field_name = f'account_{account.id}'
                self.fields[field_name] = forms.DecimalField(
                    max_digits=15,
                    decimal_places=2,
                    required=False,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'step': '0.01',
                        'min': '0',
                        'placeholder': f'Enter current value for {account.account_abbr} (optional)'
                    }),
                    label=f'{account.bank_name} - {account.account_abbr}',
                    help_text=f'{account.get_account_type_display()} Account - Market Value (Optional)'
                )
                
                # Booking value field for investment accounts
                if account.account_type == 'INVESTMENT':
                    booking_field_name = f'booking_{account.id}'
                    self.fields[booking_field_name] = forms.DecimalField(
                        max_digits=15,
                        decimal_places=2,
                        required=False,
                        widget=forms.NumberInput(attrs={
                            'class': 'form-control',
                            'step': '0.01',
                            'min': '0',
                            'placeholder': f'Enter booking value for {account.account_abbr} (optional)'
                        }),
                        label=f'{account.bank_name} - {account.account_abbr} (Booking Value)',
                        help_text='Original cost basis (Optional)'
                    )
    
    def get_account_values(self):
        """Extract account values from form data"""
        account_values = {}
        booking_values = {}
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith('account_') and value is not None:
                account_id = field_name.replace('account_', '')
                account_values[int(account_id)] = value
            elif field_name.startswith('booking_') and value is not None:
                account_id = field_name.replace('booking_', '')
                booking_values[int(account_id)] = value
        return account_values, booking_values
