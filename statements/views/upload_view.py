from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
import json
import logging

from ..models import Account, InvestmentData
from ..factory import StatementParserFactory
from ..forms import StatementUploadForm
from ..validators import validate_file_extension, validate_file_size
from ..exceptions import StatementParsingError

logger = logging.getLogger(__name__)


@login_required
def upload_statement(request):
    """Upload and parse bank statement"""
    if request.method == 'POST':
        form = StatementUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Get account
                account = form.cleaned_data.get('account')
                
                # Check if this is an investment account
                is_investment_account = account.account_type == 'INVESTMENT'
                
                if is_investment_account:
                    # Handle investment account - no file upload, just investment data
                    InvestmentData.objects.create(
                        account=account,
                        book_cost=form.cleaned_data.get('book_cost'),
                        market_value=form.cleaned_data.get('market_value')
                    )
                    
                    messages.success(
                        request, 
                        f'Successfully created investment record for {account.bank_name} - {account.account_abbr}'
                    )
                    
                    # Redirect to a different page since we don't have a statement
                    return redirect('statements:index')
                else:
                    # Handle regular bank statement upload
                    uploaded_file = request.FILES['source_file']

                    # Validate file
                    try:
                        validate_file_extension(uploaded_file)
                        validate_file_size(uploaded_file)
                    except ValidationError as e:
                        messages.error(request, str(e))
                        return redirect('upload_statement')

                    # Read file content
                    file_content = uploaded_file.read()

                    # Parse the statement
                    parser_factory = StatementParserFactory()
                    statement_meta, transactions = parser_factory.parse_statement(
                        file_content, uploaded_file.name
                    )
                    
                    # Create the statement record (save the filename)
                    from ..models import Statement, StatementDetail
                    statement = Statement.objects.create(
                        account=account,
                        source_file=uploaded_file.name,  # Save just the filename
                        statement_from_date=form.cleaned_data.get('statement_from_date') or statement_meta['statement_from_date'],
                        statement_to_date=form.cleaned_data.get('statement_to_date') or statement_meta['statement_to_date'],
                        statement_type=statement_meta['statement_type']
                    )
                    
                    # Create transaction details
                    for transaction_data in transactions:
                        StatementDetail.objects.create(
                            statement=statement,
                            item=transaction_data['item'],
                            transaction_date=transaction_data['transaction_date'],
                            amount=transaction_data['amount'],
                            direction=transaction_data['direction']
                        )
                    
                    messages.success(
                        request, 
                        f'Successfully uploaded statement with {len(transactions)} transactions'
                    )
                
                return redirect('statement_detail', statement_id=statement.id)

            except StatementParsingError as e:
                logger.error(f"Statement parsing error: {e}", exc_info=True)
                messages.error(request, f'Error parsing statement: {str(e)}')
            except ValidationError as e:
                logger.warning(f"Validation error: {e}")
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Unexpected error processing statement: {e}", exc_info=True)
                messages.error(request, f'Unexpected error processing statement. Please try again or contact support.')
    else:
        form = StatementUploadForm()
    
    # Get account data for JavaScript
    accounts_data = []
    for account in Account.objects.all():
        accounts_data.append({
            'id': account.id,
            'account_type': account.account_type
        })
    
    return render(request, 'statements/upload.html', {
        'form': form,
        'accounts_data': accounts_data
    })
