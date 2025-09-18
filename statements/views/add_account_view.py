from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..forms.add_account_form import AddAccountForm


@login_required
def add_account(request):
    """Add a new bank account"""
    if request.method == 'POST':
        form = AddAccountForm(request.POST)
        if form.is_valid():
            try:
                account = form.save()
                messages.success(
                    request, 
                    f'Successfully created account: {account.bank_name} - {account.account_abbr}'
                )
                return redirect('statements:index')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
    else:
        form = AddAccountForm()
    
    return render(request, 'statements/add_account.html', {
        'form': form
    })
