from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ..models import Statement


@login_required
def statement_list(request):
    """List all statements"""
    statements = Statement.objects.select_related('account').all()
    
    context = {
        'statements': statements,
    }
    
    return render(request, 'statements/statement_list.html', context)
