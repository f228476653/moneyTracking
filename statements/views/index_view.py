from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ..models import Statement


@login_required
def index(request):
    """Home page with recent statements"""
    # Get recent statements
    recent_statements = Statement.objects.select_related('account').all()[:5]
    
    context = {
        'recent_statements': recent_statements,
    }
    
    return render(request, 'statements/index.html', context)
