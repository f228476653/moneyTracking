from django.shortcuts import render
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.db import models
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from decimal import Decimal
import plotly.graph_objs as go
import plotly.utils

from ..models import StatementDetail, Account, AccountValue, InvestmentData


@login_required
def reports(request):
    """Generate various financial reports"""
    # Get filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Get transactions with filters
    transactions = StatementDetail.objects.all()
    
    # Apply date range filter
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            transactions = transactions.filter(transaction_date__range=[start, end])
        except ValueError:
            transactions = StatementDetail.objects.all()
    else:
        # Default to previous month (1st to end of month)
        today = timezone.now().date()
        # Get first day of current month
        first_day_current = today.replace(day=1)
        # Get last day of previous month
        last_day_previous = first_day_current - timedelta(days=1)
        # Get first day of previous month
        first_day_previous = last_day_previous.replace(day=1)
        
        start = first_day_previous
        end = last_day_previous
        transactions = transactions.filter(transaction_date__range=[start, end])
    
    # Calculate bank-specific totals (will be calculated in Bank Account Summary section)
    total_bank_income = Decimal('0.00')
    total_bank_spending = Decimal('0.00')
    
    
    # CREDIT transactions (all transactions from credit card accounts)
    credit_transactions = transactions.filter(
        statement__account__account_type='CREDIT_CARD'
    ).order_by('-transaction_date')
    
    credit_total = credit_transactions.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    # BANK account dashboard with same categorization logic as home page
    bank_accounts = Account.objects.filter(account_type='BANK')
    bank_by_account = {}
    for account in bank_accounts:
        account_transactions = transactions.filter(statement__account=account)
        
        # Apply same categorization logic as home page
        income = Decimal('0.00')
        spending = Decimal('0.00')
        investments = Decimal('0.00')
        transfers = Decimal('0.00')
        
        # Store detailed transactions for each category
        income_transactions = []
        spending_transactions = []
        investment_transactions = []
        transfer_transactions = []
        
        for transaction in account_transactions:
            # Check if it's a transfer (EQ BANK or PAY EMP-VENDOR) - only OUT direction
            is_transfer = (
                transaction.direction == 'OUT' and (
                    'EQ BANK' in transaction.item.upper() or 
                    'PAY EMP-VENDOR' in transaction.item.upper()
                )
            )
            
            # Check if it's an investment transaction (only OUT direction transactions)
            is_investment = (
                transaction.direction == 'OUT' and (
                    'INVESTMENTS' in transaction.item.upper() or 
                    'QUESTRADE' in transaction.item.upper() or 
                    'MUTUAL FUNDS' in transaction.item.upper() or 
                    'GIC' in transaction.item.upper()
                )
            )
            
            # Check if it's spending (outgoing but not investment or transfer)
            is_spending = (
                transaction.direction == 'OUT' and 
                not ('INVESTMENTS' in transaction.item.upper() or 'QUESTRADE' in transaction.item.upper() or 'MUTUAL FUNDS' in transaction.item.upper() or 'GIC' in transaction.item.upper()) and
                not is_transfer
            )
            
            # Check if it's income (all IN direction transactions, excluding GIC)
            is_income = (transaction.direction == 'IN' and not (
                'GIC' in transaction.item.upper()
            ))
            
            transaction_data = {
                'id': transaction.id,
                'item': transaction.item,
                'amount': float(transaction.amount),
                'date': transaction.transaction_date.strftime('%Y-%m-%d'),
                'direction': transaction.direction
            }
            
            if is_transfer:
                transfers += transaction.amount
                transfer_transactions.append(transaction_data)
            elif is_investment:
                investments += transaction.amount
                investment_transactions.append(transaction_data)
            elif is_spending:
                spending += transaction.amount
                spending_transactions.append(transaction_data)
            elif is_income:
                income += transaction.amount
                income_transactions.append(transaction_data)
        
        bank_by_account[account] = {
            'income': income,
            'spending': spending,
            'investments': investments,
            'transfers': transfers,
            'net_amount': income - spending - transfers,
            'transaction_count': account_transactions.count(),
            'transactions': account_transactions[:10],  # Last 10 transactions
            'income_transactions': income_transactions,
            'spending_transactions': spending_transactions,
            'investment_transactions': investment_transactions,
            'transfer_transactions': transfer_transactions
        }
        
        # Add to total bank amounts (subtract transfers from income since they're not real income)
        total_bank_income += income - transfers
        total_bank_spending += spending
    
    # CREDIT CARD account dashboard
    credit_accounts = Account.objects.filter(account_type='CREDIT_CARD')
    credit_by_account = {}
    total_credit_spending = Decimal('0.00')
    
    for account in credit_accounts:
        account_transactions = transactions.filter(statement__account=account)
        
        # For credit cards: OUT = spending, IN = refunds/payments
        # We want: spending - refunds (OUT - IN)
        account_spending = account_transactions.filter(direction='OUT').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        # Exclude ROYAL BANK OF CANADA TORONTO transactions from refund calculations
        account_refunds = account_transactions.filter(
            direction='IN'
        ).exclude(
            item__icontains='ROYAL BANK OF CANADA TORONTO'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        net_spending = account_spending - account_refunds
        
        # Get detailed transactions for spending and refunds
        spending_transactions = []
        refund_transactions = []
        
        for transaction in account_transactions:
            transaction_data = {
                'id': transaction.id,
                'item': transaction.item,
                'amount': float(transaction.amount),
                'date': transaction.transaction_date.strftime('%Y-%m-%d'),
                'direction': transaction.direction
            }
            
            if transaction.direction == 'OUT':
                spending_transactions.append(transaction_data)
            elif transaction.direction == 'IN':
                # Exclude ROYAL BANK OF CANADA TORONTO transactions from refunds
                if 'ROYAL BANK OF CANADA TORONTO' not in transaction.item.upper():
                    refund_transactions.append(transaction_data)
        
        credit_by_account[account] = {
            'spending': account_spending,
            'refunds': account_refunds,
            'net_spending': net_spending,
            'transaction_count': account_transactions.count(),
            'transactions': account_transactions[:10],  # Last 10 transactions
            'spending_transactions': spending_transactions,
            'refund_transactions': refund_transactions
        }
        
        total_credit_spending += net_spending
    
    # INVESTMENT account dashboard
    investment_accounts = Account.objects.filter(account_type='INVESTMENT')
    investment_transactions = transactions.filter(
        statement__account__account_type='INVESTMENT'
    ).order_by('-transaction_date')
    
    investment_total = investment_transactions.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    # Investment performance by account
    investment_by_account = {}
    for account in investment_accounts:
        account_transactions = investment_transactions.filter(statement__account=account)
        account_total = account_transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        investment_by_account[account] = {
            'total': account_total,
            'transaction_count': account_transactions.count(),
            'transactions': account_transactions[:10]  # Last 10 transactions
        }
    
    
    # Monthly chart data for the current year
    current_year = timezone.now().year
    monthly_transactions = StatementDetail.objects.filter(
        statement__account__account_type='BANK',
        transaction_date__year=current_year
    ).select_related('statement__account')
    
    # Prepare data for monthly chart
    months = list(range(1, 13))
    spending = [0] * 12
    investments = [0] * 12
    income = [0] * 12
    transfers = [0] * 12
    monthly_details = {}
    
    # Initialize monthly details structure
    for month in range(1, 13):
        monthly_details[month] = {
            'spending': [],
            'investments': [],
            'income': [],
            'transfers': []
        }
    
    # Group transactions by month and categorize
    for transaction in monthly_transactions:
        month_idx = transaction.transaction_date.month - 1
        month = transaction.transaction_date.month
        
        # Check if it's a transfer (EQ BANK or PAY EMP-VENDOR) - only OUT direction
        is_transfer = (
            transaction.direction == 'OUT' and (
                'EQ BANK' in transaction.item.upper() or 
                'PAY EMP-VENDOR' in transaction.item.upper()
            )
        )
        
        # Check if it's an investment transaction (only OUT direction transactions)
        is_investment = (
            transaction.direction == 'OUT' and (
                'INVESTMENTS' in transaction.item.upper() or 
                'QUESTRADE' in transaction.item.upper() or 
                'MUTUAL FUNDS' in transaction.item.upper() or 
                'GIC' in transaction.item.upper()
            )
        )
        
        # Check if it's spending (outgoing but not investment or transfer)
        is_spending = (
            transaction.direction == 'OUT' and 
            not ('INVESTMENTS' in transaction.item.upper() or 'QUESTRADE' in transaction.item.upper() or 'MUTUAL FUNDS' in transaction.item.upper() or 'GIC' in transaction.item.upper()) and
            not is_transfer
        )
        
        # Check if it's income (all IN direction transactions, excluding GIC)
        is_income = (transaction.direction == 'IN' and not (
            'GIC' in transaction.item.upper()
        ))
        
        transaction_data = {
            'item': transaction.item,
            'amount': float(transaction.amount),
            'date': transaction.transaction_date.strftime('%Y-%m-%d'),
            'direction': transaction.direction,
            'account': {
                'bank_name': transaction.statement.account.bank_name,
                'account_abbr': transaction.statement.account.account_abbr,
                'account_number': transaction.statement.account.account_number
            }
        }
        
        if is_transfer:
            transfers[month_idx] += float(transaction.amount)
            monthly_details[month]['transfers'].append(transaction_data)
        elif is_investment:
            investments[month_idx] += float(transaction.amount)
            monthly_details[month]['investments'].append(transaction_data)
        elif is_spending:
            spending[month_idx] += float(transaction.amount)
            monthly_details[month]['spending'].append(transaction_data)
        elif is_income:
            income[month_idx] += float(transaction.amount)
            monthly_details[month]['income'].append(transaction_data)
    
    # Create monthly chart
    monthly_chart = go.Figure()
    monthly_chart.add_trace(go.Bar(
        x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        y=income,
        name='Income',
        marker_color='#3498db'
    ))
    monthly_chart.add_trace(go.Bar(
        x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        y=spending,
        name='Actual Spending',
        marker_color='#e74c3c'
    ))
    monthly_chart.add_trace(go.Bar(
        x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        y=investments,
        name='Investments',
        marker_color='#27ae60'
    ))
    monthly_chart.add_trace(go.Bar(
        x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        y=transfers,
        name='Transfers',
        marker_color='#f39c12'
    ))
    monthly_chart.update_layout(
        title=f'Monthly Income, Spending, Investments & Transfers - {current_year}',
        xaxis_title='Month',
        yaxis_title='Amount ($)',
        barmode='group',
        yaxis=dict(
            tickformat=',.2f',
            separatethousands=True
        ),
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1
        )
    )
    
    context = {
        'start_date': start_date or start.strftime('%Y-%m-%d'),
        'end_date': end_date or end.strftime('%Y-%m-%d'),
        'total_ins': total_bank_income,
        'total_outs': total_bank_spending,  # Bank spending only
        'total_spending': total_bank_spending,  # Bank spending only
        'net_amount': total_bank_income - total_bank_spending,
        # Bank tab data
        'bank_accounts': bank_by_account,
        # Credit card tab data
        'credit_transactions': credit_transactions,
        'credit_total': credit_total,
        'credit_accounts': credit_by_account,
        'total_credit_spending': total_credit_spending,
        # Investment tab data
        'investment_accounts': investment_accounts,
        'investment_transactions': investment_transactions,
        'investment_total': investment_total,
        'investment_by_account': investment_by_account,
        # Monthly chart data
        'monthly_chart': plotly.utils.PlotlyJSONEncoder().encode(monthly_chart),
        'monthly_details': monthly_details,
    }
    
    return render(request, 'statements/reports.html', context)
