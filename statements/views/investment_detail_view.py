from django.shortcuts import render
from django.db.models import Sum, Q
from django.contrib.auth.decorators import login_required
from decimal import Decimal
import plotly.graph_objs as go
import plotly.utils

from ..models import Account, AccountValue
from ..forms import InvestmentFilterForm


@login_required
def investment_detail(request):
    """Investment detail report showing summary of all investment data from account values"""
    
    # Initialize filter form
    filter_form = InvestmentFilterForm(request.GET)
    
    # Get all investment accounts
    investment_accounts = Account.objects.filter(account_type='INVESTMENT')
    
    # Get all bank accounts
    bank_accounts = Account.objects.filter(account_type='BANK')
    
    all_investment_values = AccountValue.objects.filter(
        account__account_type='INVESTMENT'
    ).select_related('account').order_by('account', '-date', '-date_updated')
    
    all_bank_values = AccountValue.objects.filter(
        account__account_type='BANK'
    ).select_related('account').order_by('account', '-date', '-date_updated')
    
    investment_account_values = []
    seen_investment_accounts = set()
    for av in all_investment_values:
        if av.account.id not in seen_investment_accounts:
            investment_account_values.append(av)
            seen_investment_accounts.add(av.account.id)
    
    bank_account_values = []
    seen_bank_accounts = set()
    for av in all_bank_values:
        if av.account.id not in seen_bank_accounts:
            bank_account_values.append(av)
            seen_bank_accounts.add(av.account.id)
    
    account_values = investment_account_values
    
    # Apply filters if form is valid
    if filter_form.is_valid():
        start_date = filter_form.cleaned_data.get('start_date')
        end_date = filter_form.cleaned_data.get('end_date')
        account_filter = filter_form.cleaned_data.get('account_filter')
        
        if start_date:
            account_values = [av for av in account_values if av.date >= start_date]
        if end_date:
            account_values = [av for av in account_values if av.date <= end_date]
        
        if account_filter:
            account_values = [av for av in account_values if av.account == account_filter]
    else:
        print(f"Form errors: {filter_form.errors}")
        print(f"Form data: {filter_form.data}")
    
    total_booking_value = sum(
        (av.booking_value or Decimal('0.00')) for av in account_values
    )
    total_market_value = sum(
        (av.current_value or Decimal('0.00')) for av in account_values
    )
    total_gain_loss = total_market_value - total_booking_value
    
    if total_booking_value > 0:
        total_gain_loss_percentage = (total_gain_loss / total_booking_value) * 100
    else:
        total_gain_loss_percentage = Decimal('0.00')
    
    total_bank_amount = sum(
        (av.current_value or Decimal('0.00')) for av in bank_account_values
    )
    
    total_investment_amount = total_market_value
    
    # Calculate total values - only include accounts that have values
    total_values = total_bank_amount + total_investment_amount
    
    account_summaries = []
    filtered_accounts = investment_accounts
    if filter_form.is_valid() and filter_form.cleaned_data.get('account_filter'):
        filtered_accounts = [filter_form.cleaned_data.get('account_filter')]
    
    for account in filtered_accounts:
        account_value = next((av for av in account_values if av.account == account), None)
        if account_value:
            booking_value = account_value.booking_value or Decimal('0.00')
            market_value = account_value.current_value or Decimal('0.00')
            gain_loss = market_value - booking_value
            
            if booking_value > 0:
                gain_loss_percentage = (gain_loss / booking_value) * 100
            else:
                gain_loss_percentage = Decimal('0.00')
            
            account_summaries.append({
                'account': account,
                'book_cost': booking_value,
                'market_value': market_value,
                'gain_loss': gain_loss,
                'gain_loss_percentage': gain_loss_percentage,
                'latest_update': account_value.date_updated
            })
    
    account_summaries.sort(key=lambda x: x['market_value'], reverse=True)
    
    investment_value_chart = None
    if investment_accounts.exists():
        all_chart_values = AccountValue.objects.filter(
            account__account_type='INVESTMENT'
        ).select_related('account').order_by('date', 'date_updated')
        
        if filter_form.is_valid():
            start_date = filter_form.cleaned_data.get('start_date')
            end_date = filter_form.cleaned_data.get('end_date')
            account_filter = filter_form.cleaned_data.get('account_filter')
            
            if start_date:
                all_chart_values = all_chart_values.filter(date__gte=start_date)
            if end_date:
                all_chart_values = all_chart_values.filter(date__lte=end_date)
            
            if account_filter:
                all_chart_values = all_chart_values.filter(account=account_filter)
        
        if all_chart_values.exists():
            investment_chart = go.Figure()
            
            accounts_data = {}
            
            account_date_values = {}
            
            for value in all_chart_values:
                account_key = f"{value.account.bank_name} - {value.account.account_abbr}"
                # Use the date field instead of date_updated for proper grouping
                date_str = str(value.date)
                
                if account_key not in account_date_values:
                    account_date_values[account_key] = {}
                
                # Use date for grouping, but keep datetime for comparison when same date
                if date_str not in account_date_values[account_key] or value.date_updated > account_date_values[account_key][date_str]['datetime']:
                    account_date_values[account_key][date_str] = {
                        'datetime': value.date_updated,
                        'date': value.date,
                        'market_value': float(value.current_value),
                        'booking_value': float(value.booking_value or 0)
                    }
            
            for account_key, date_data in account_date_values.items():
                accounts_data[account_key] = {
                    'dates': [],
                    'market_values': [],
                    'booking_values': []
                }
                
                sorted_dates = sorted(date_data.keys())
                for date_str in sorted_dates:
                    accounts_data[account_key]['dates'].append(date_str)
                    accounts_data[account_key]['market_values'].append(date_data[date_str]['market_value'])
                    accounts_data[account_key]['booking_values'].append(date_data[date_str]['booking_value'])
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            for i, (account_name, data) in enumerate(accounts_data.items()):
                color = colors[i % len(colors)]
                
                investment_chart.add_trace(go.Scatter(
                    x=data['dates'],
                    y=data['market_values'],
                    mode='lines+markers',
                    name=f'{account_name} (Market Value)',
                    line=dict(color=color, width=3),
                    marker=dict(size=8, symbol='circle')
                ))
                
                investment_chart.add_trace(go.Scatter(
                    x=data['dates'],
                    y=data['booking_values'],
                    mode='lines+markers',
                    name=f'{account_name} (Booking Value)',
                    line=dict(color=color, width=3, dash='dash'),
                    marker=dict(size=6, symbol='diamond')
                ))
            
            investment_chart.update_layout(
                title='Investment Account Values Over Time',
                xaxis_title='Date',
                yaxis_title='Value ($)',
                hovermode='x unified',
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.01
                ),
                yaxis=dict(
                    tickformat=',.2f',
                    separatethousands=True
                ),
                height=500
            )
            
            investment_value_chart = plotly.utils.PlotlyJSONEncoder().encode(investment_chart)
    
    total_values_chart = None
    if bank_accounts.exists() or investment_accounts.exists():
        all_total_values = AccountValue.objects.filter(
            account__account_type__in=['BANK', 'INVESTMENT']
        ).select_related('account').order_by('date', 'date_updated')
        
        # Apply filters if form is valid
        if filter_form.is_valid():
            start_date = filter_form.cleaned_data.get('start_date')
            end_date = filter_form.cleaned_data.get('end_date')
            account_filter = filter_form.cleaned_data.get('account_filter')
            
            if start_date:
                all_total_values = all_total_values.filter(date__gte=start_date)
            if end_date:
                all_total_values = all_total_values.filter(date__lte=end_date)
            
            # If account filter is set, only show that account (and bank accounts if it's an investment account)
            if account_filter:
                # If filtering by an investment account, still include all bank accounts
                if account_filter.account_type == 'INVESTMENT':
                    all_total_values = all_total_values.filter(
                        Q(account=account_filter) | Q(account__account_type='BANK')
                    )
                else:
                    # If filtering by a bank account, only show that account
                    all_total_values = all_total_values.filter(account=account_filter)
        
        if all_total_values.exists():
            # Get all distinct dates that have entries
            all_dates = set()
            all_accounts = set()
            account_values_by_date = {}
            
            # First pass: collect all dates and accounts, and group values by date
            for value in all_total_values:
                # Use the date field instead of date_updated for proper grouping
                date_str = str(value.date)
                account_id = value.account.id
                all_dates.add(date_str)
                all_accounts.add(account_id)
                
                if date_str not in account_values_by_date:
                    account_values_by_date[date_str] = []
                
                account_values_by_date[date_str].append({
                    'account_id': account_id,
                    'account_type': value.account.account_type,
                    'current_value': value.current_value or Decimal('0.00'),
                    'datetime': value.date_updated,
                    'date': value.date
                })
            
            # For each date, keep only the latest value per account (remove duplicates on same date)
            for date_str in account_values_by_date:
                account_latest = {}
                for value_data in account_values_by_date[date_str]:
                    account_id = value_data['account_id']
                    if account_id not in account_latest or value_data['datetime'] > account_latest[account_id]['datetime']:
                        account_latest[account_id] = value_data
                account_values_by_date[date_str] = list(account_latest.values())
            
            # Now create snapshots: for each date, include all accounts with their latest value up to that date
            sorted_dates = sorted(all_dates)
            date_totals = {}
            
            for date_str in sorted_dates:
                # For this date, get the latest value for each account up to this date
                account_snapshot = {}
                
                # Check all dates up to and including this date
                for check_date in sorted_dates:
                    if check_date > date_str:
                        break
                    
                    # Get values from this date
                    if check_date in account_values_by_date:
                        for value_data in account_values_by_date[check_date]:
                            account_id = value_data['account_id']
                            # Use this value if we don't have one yet, or if this date is more recent
                            # Compare by date field, not date_updated
                            if account_id not in account_snapshot or value_data['date'] > account_snapshot[account_id]['date']:
                                account_snapshot[account_id] = value_data
                
                # Now aggregate totals for this date
                date_totals[date_str] = {
                    'datetime': None,
                    'bank_total': Decimal('0.00'),
                    'investment_total': Decimal('0.00'),
                    'total_value': Decimal('0.00')
                }
                
                for account_id, value_data in account_snapshot.items():
                    # Update datetime to the most recent one
                    if date_totals[date_str]['datetime'] is None or value_data['datetime'] > date_totals[date_str]['datetime']:
                        date_totals[date_str]['datetime'] = value_data['datetime']
                    
                    # Add to appropriate total
                    if value_data['account_type'] == 'BANK':
                        date_totals[date_str]['bank_total'] += value_data['current_value']
                    elif value_data['account_type'] == 'INVESTMENT':
                        date_totals[date_str]['investment_total'] += value_data['current_value']
                
                date_totals[date_str]['total_value'] = date_totals[date_str]['bank_total'] + date_totals[date_str]['investment_total']
            
            # Sort dates for the chart
            chart_dates = sorted(date_totals.keys())
            
            if chart_dates:
                trend_chart = go.Figure()
                
                dates = []
                bank_totals = []
                investment_totals = []
                total_values_list = []
                
                for date_str in chart_dates:
                    data = date_totals[date_str]
                    dates.append(date_str)
                    bank_totals.append(float(data['bank_total']))
                    investment_totals.append(float(data['investment_total']))
                    total_values_list.append(float(data['total_value']))
                
                trend_chart.add_trace(go.Scatter(
                    x=dates,
                    y=bank_totals,
                    mode='lines+markers',
                    name='Bank Accounts',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8, symbol='circle')
                ))
                
                trend_chart.add_trace(go.Scatter(
                    x=dates,
                    y=investment_totals,
                    mode='lines+markers',
                    name='Investment Accounts',
                    line=dict(color='#ff7f0e', width=3),
                    marker=dict(size=8, symbol='circle')
                ))
                
                trend_chart.add_trace(go.Scatter(
                    x=dates,
                    y=total_values_list,
                    mode='lines+markers',
                    name='Total Values',
                    line=dict(color='#2ca02c', width=4),
                    marker=dict(size=10, symbol='diamond')
                ))
                
                trend_chart.update_layout(
                    title='Total Account Values Trend',
                    xaxis_title='Date',
                    yaxis_title='Value ($)',
                    hovermode='x unified',
                    legend=dict(
                        orientation="v",
                        yanchor="top",
                        y=1,
                        xanchor="left",
                        x=1.01
                    ),
                    yaxis=dict(
                        tickformat=',.2f',
                        separatethousands=True
                    ),
                    height=500
                )
                
                total_values_chart = plotly.utils.PlotlyJSONEncoder().encode(trend_chart)
    
    # Prepare detailed account data for clickable functionality
    bank_account_details = []
    for account in bank_accounts:
        account_value = next((av for av in bank_account_values if av.account == account), None)
        if account_value:
            bank_account_details.append({
                'account': {
                    'id': account.id,
                    'bank_name': account.bank_name,
                    'account_abbr': account.account_abbr,
                    'account_number': account.account_number
                },
                'current_value': float(account_value.current_value or Decimal('0.00')),
                'latest_update': account_value.date_updated.isoformat(),
                'account_count': 1
            })
    
    investment_account_details = []
    for account in investment_accounts:
        account_value = next((av for av in investment_account_values if av.account == account), None)
        if account_value:
            investment_account_details.append({
                'account': {
                    'id': account.id,
                    'bank_name': account.bank_name,
                    'account_abbr': account.account_abbr,
                    'account_number': account.account_number
                },
                'current_value': float(account_value.current_value or Decimal('0.00')),
                'booking_value': float(account_value.booking_value or Decimal('0.00')),
                'latest_update': account_value.date_updated.isoformat(),
                'account_count': 1
            })
    
    # Ensure all total values are properly formatted for template compatibility
    if total_bank_amount is None:
        total_bank_amount = Decimal('0.00')
    elif isinstance(total_bank_amount, Decimal):
        total_bank_amount = float(total_bank_amount)
        
    if total_investment_amount is None:
        total_investment_amount = Decimal('0.00')
    elif isinstance(total_investment_amount, Decimal):
        total_investment_amount = float(total_investment_amount)
        
    if total_values is None:
        total_values = Decimal('0.00')
    elif isinstance(total_values, Decimal):
        # Convert to float for template compatibility
        total_values = float(total_values)
    
    context = {
        'investment_accounts': investment_accounts,
        'account_summaries': account_summaries,
        'total_book_cost': total_booking_value,
        'total_market_value': total_market_value,
        'total_gain_loss': total_gain_loss,
        'total_gain_loss_percentage': total_gain_loss_percentage,
        'total_investments': len(account_summaries),
        'filter_form': filter_form,
        'investment_value_chart': investment_value_chart,
        'total_bank_amount': total_bank_amount,
        'total_investment_amount': total_investment_amount,
        'total_values': total_values,
        'total_values_chart': total_values_chart,
        'bank_account_details': bank_account_details,
        'investment_account_details': investment_account_details,
    }
    
    return render(request, 'statements/investment_detail.html', context)
