from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal

from ..models import Account, AccountValue
from ..forms import AccountValueForm


@login_required
def account_values(request):
    """Page for updating current values of all BANK and INVESTMENT accounts"""
    
    # Get all BANK and INVESTMENT accounts
    accounts = Account.objects.filter(account_type__in=['BANK', 'INVESTMENT']).order_by('account_type', 'bank_name', 'account_abbr')
    
    if request.method == 'POST':
        form = AccountValueForm(request.POST, accounts=accounts)
        if form.is_valid():
            account_values, booking_values = form.get_account_values()
            
            # Create AccountValue records for each account
            created_count = 0
            for account_id, value in account_values.items():
                if value is not None:
                    account = Account.objects.get(id=account_id)
                    booking_value = booking_values.get(account_id)
                    
                    AccountValue.objects.create(
                        account=account,
                        current_value=value,
                        booking_value=booking_value
                    )
                    created_count += 1
            
            messages.success(
                request, 
                f'Successfully updated current values for {created_count} account(s).'
            )
            
            return redirect('statements:account_values')
    else:
        form = AccountValueForm(accounts=accounts)
    
    # Get current values for display
    current_values = {}
    for account in accounts:
        latest_value = AccountValue.objects.filter(account=account).order_by('-date_updated').first()
        if latest_value:
            current_values[account.id] = {
                'value': latest_value.current_value,
                'booking_value': latest_value.booking_value,
                'date': latest_value.date_updated.date()
            }
    
    # Calculate totals
    total_bank_value = Decimal('0.00')
    total_investment_value = Decimal('0.00')
    
    for account in accounts:
        if account.id in current_values:
            value = current_values[account.id]['value']
            if account.account_type == 'BANK':
                total_bank_value += value
            elif account.account_type == 'INVESTMENT':
                total_investment_value += value
    
    total_value = total_bank_value + total_investment_value
    
    context = {
        'accounts': accounts,
        'form': form,
        'current_values': current_values,
        'total_bank_value': total_bank_value,
        'total_investment_value': total_investment_value,
        'total_value': total_value,
    }
    
    return render(request, 'statements/account_values.html', context)
