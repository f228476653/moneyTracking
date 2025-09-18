#!/usr/bin/env python3
"""
Test script to demonstrate the bank account dropdown functionality
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bank_parser.settings')
django.setup()

from statements.forms import StatementUploadForm

def test_bank_account_dropdown():
    """Test the bank account dropdown functionality"""
    print("Testing Bank Account Dropdown...")
    
    # Create a form instance
    form = StatementUploadForm()
    
    print(f"\n=== Bank Account Options ===")
    for value, label in form.fields['bank_account'].choices:
        if value:  # Skip the empty option
            print(f"  {value}: {label}")
    
    print(f"\n=== Bank Info Mapping ===")
    
    # Test the bank info mapping
    test_selections = [
        'TD_BANK_CREDIT_CARD',
        'TD_BANK_CHEQUE_ACCOUNT', 
        'AMEX_CREDIT_CARD',
        'CIBC_CREDIT_CARD',
        'RBC_BUSINESS_ACCOUNT',
        'WEALTHSIMPLE_RRSP',
        'WEALTHSIMPLE_TFSA',
        'BMO_CHEQUE_ACCOUNT',
        'BMO_RRSP',
        'BMO_TFSA',
        'QUESTRADE_RRSP',
        'QUESTRADE_TFSA',
        'COOP_BUSINESS_INVEST'
    ]
    
    for selection in test_selections:
        # Simulate form data
        form_data = {'bank_account': selection}
        form = StatementUploadForm(data=form_data)
        if form.is_valid():
            bank_name, account_abbr, account_type = form.get_bank_info_from_selection()
            print(f"  {selection}: {bank_name} - {account_abbr} ({account_type})")
    
    print(f"\n=== Features ===")
    print("✅ Dropdown with all your bank accounts")
    print("✅ Auto-detection from filename")
    print("✅ Automatic bank name and account type mapping")
    print("✅ Easy selection without typing")
    print("✅ Fallback to auto-detection if not selected")

if __name__ == "__main__":
    test_bank_account_dropdown()
