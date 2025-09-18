from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
import plotly.graph_objs as go
import plotly.utils

from ..models import Statement


@login_required
def statement_detail(request, statement_id):
    """View detailed information about a specific statement"""
    statement = get_object_or_404(Statement.objects.select_related('account'), id=statement_id)
    transactions = statement.statementdetail_set.all()
    
    # Get transaction summary
    total_ins = statement.total_in
    total_outs = statement.total_out
    net_amount = statement.net_amount
    
    # Create transaction chart
    if transactions:
        dates = [t.transaction_date for t in transactions]
        amounts = [float(t.amount) for t in transactions]
        colors = ['green' if t.direction == 'IN' else 'red' for t in transactions]
        
        transaction_chart = go.Figure()
        transaction_chart.add_trace(go.Scatter(
            x=dates,
            y=amounts,
            mode='markers',
            marker=dict(
                color=colors,
                size=8
            ),
            text=[f"{t.item}: ${t.amount}" for t in transactions],
            hovertemplate='<b>%{text}</b><br>' +
                         'Date: %{x}<br>' +
                         'Amount: $%{y:,.2f}<br>' +
                         '<extra></extra>'
        ))
        transaction_chart.update_layout(
            title='Transaction Timeline',
            xaxis_title='Date',
            yaxis_title='Amount ($)',
            hovermode='closest',
            yaxis=dict(
                tickformat=',.2f',
                separatethousands=True
            )
        )
        
        chart_json = plotly.utils.PlotlyJSONEncoder().encode(transaction_chart)
    else:
        chart_json = None
    
    context = {
        'statement': statement,
        'transactions': transactions,
        'total_ins': total_ins,
        'total_outs': total_outs,
        'net_amount': net_amount,
        'transaction_chart': chart_json,
    }
    
    return render(request, 'statements/statement_detail.html', context)
