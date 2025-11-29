from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import IntegrityError
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
            
            # Create or update AccountValue records for each account
            created_count = 0
            updated_count = 0
            error_count = 0
            today = timezone.now().date()
            
            for account_id, value in account_values.items():
                if value is not None:
                    account = Account.objects.get(id=account_id)
                    booking_value = booking_values.get(account_id)
                    
                    # Check if an entry already exists for this account and date
                    existing_value = AccountValue.objects.filter(
                        account=account,
                        date=today
                    ).first()
                    
                    if existing_value:
                        # Update existing entry
                        existing_value.current_value = value
                        if booking_value is not None:
                            existing_value.booking_value = booking_value
                        try:
                            existing_value.save()
                            updated_count += 1
                        except IntegrityError:
                            error_count += 1
                            messages.error(
                                request,
                                f'❌ Error updating {account.account_abbr}: A duplicate entry already exists for today.'
                            )
                    else:
                        # Create new entry
                        try:
                            AccountValue.objects.create(
                                account=account,
                                current_value=value,
                                booking_value=booking_value,
                                date=today
                            )
                            created_count += 1
                        except IntegrityError:
                            error_count += 1
                            messages.error(
                                request,
                                f'❌ Error creating entry for {account.account_abbr}: A duplicate entry already exists for today.'
                            )
            
            if created_count > 0 or updated_count > 0:
                success_msg = []
                if created_count > 0:
                    success_msg.append(f'Created {created_count} new value(s)')
                if updated_count > 0:
                    success_msg.append(f'Updated {updated_count} existing value(s)')
                messages.success(
                    request, 
                    f'✅ Successfully processed values for {created_count + updated_count} account(s)! ({", ".join(success_msg)})'
                )
            elif error_count > 0:
                messages.warning(
                    request,
                    f'⚠️ {error_count} account(s) could not be processed due to duplicate entries.'
                )
            else:
                messages.info(
                    request, 
                    'No values were updated. All fields are optional - you can leave them empty if you don\'t want to update any accounts.'
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
                'date': latest_value.date
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
