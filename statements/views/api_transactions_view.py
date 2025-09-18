from django.http import JsonResponse
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from datetime import datetime

from ..models import StatementDetail


@login_required
def api_transactions(request):
    """API endpoint for getting transaction data for charts"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    transactions = StatementDetail.objects.all()
    
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            transactions = transactions.filter(transaction_date__range=[start, end])
        except ValueError:
            pass
    
    # Group by date and direction
    daily_data = transactions.values('transaction_date', 'direction').annotate(
        total=Sum('amount')
    ).order_by('transaction_date')
    
    data = {
        'dates': [],
        'ins': [],
        'outs': []
    }
    
    for item in daily_data:
        data['dates'].append(item['transaction_date'].strftime('%Y-%m-%d'))
        if item['direction'] == 'IN':
            data['ins'].append(float(item['total']))
            data['outs'].append(0)
        else:
            data['ins'].append(0)
            data['outs'].append(float(item['total']))
    
    return JsonResponse(data)
