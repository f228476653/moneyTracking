"""
American Express credit card parser for CSV statements
"""

import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Tuple
import logging
from decimal import Decimal
import decimal

from .base import BaseStatementParser

logger = logging.getLogger(__name__)


class AmexCreditCardParser(BaseStatementParser):
    """Parser specifically for American Express credit card CSV files"""
    
    def __init__(self):
        self.supported_formats = ['.csv']
    
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        """Check if this is an Amex credit card statement"""
        if not filename.lower().endswith('.csv'):
            return False
        
        try:
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = file_content.decode('latin-1')
            except UnicodeDecodeError:
                return False
        
        # Check for Amex-specific headers
        lines = content.split('\n')
        if len(lines) < 2:
            return False
        
        header_line = lines[0].strip().lower()
        amex_headers = ['date', 'date processed', 'description', 'card member', 'account #', 'amount']
        
        # Check if all Amex headers are present
        header_parts = [h.strip() for h in header_line.split(',')]
        return all(amex_header in header_parts for amex_header in amex_headers)
    
    def parse(self, file_content: bytes, filename: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Parse Amex credit card statement"""
        try:
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            content = file_content.decode('latin-1')
        
        # Parse CSV content
        csv_reader = csv.DictReader(io.StringIO(content))
        transactions = []
        
        # Get statement metadata from first few rows
        statement_meta = self._extract_statement_metadata(content, filename)
        
        for row in csv_reader:
            transaction = self._parse_amex_transaction(row)
            if transaction:
                transactions.append(transaction)
        
        return statement_meta, transactions
    
    def _extract_statement_metadata(self, content: str, filename: str) -> Dict[str, Any]:
        """Extract statement metadata from Amex CSV"""
        lines = content.split('\n')
        
        # Find date range from transactions
        dates = []
        for line in lines[1:]:  # Skip header
            if line.strip():
                parts = line.split(',')
                if len(parts) >= 1:
                    try:
                        date_str = parts[0].strip()
                        if date_str and date_str != 'Date':
                            # Parse Amex date format: "03 Aug 2025"
                            date_obj = datetime.strptime(date_str, '%d %b %Y').date()
                            dates.append(date_obj)
                    except ValueError:
                        continue
        
        # Get account info from first transaction
        account_info = self._extract_account_info(content)
        
        return {
            'bank_name': 'American Express',
            'account_number': account_info.get('account_number', 'Unknown'),
            'account_abbr': 'AMEX',
            'statement_from_date': min(dates) if dates else datetime.now().date(),
            'statement_to_date': max(dates) if dates else datetime.now().date(),
            'statement_type': 'CSV'
        }
    
    def _extract_account_info(self, content: str) -> Dict[str, str]:
        """Extract account information from Amex CSV"""
        lines = content.split('\n')
        
        for line in lines[1:]:  # Skip header
            if line.strip():
                parts = line.split(',')
                if len(parts) >= 5:  # Should have Account # column
                    account_num = parts[4].strip()
                    if account_num and account_num != 'Account #':
                        return {'account_number': account_num}
        
        return {'account_number': 'Unknown'}
    
    def _parse_amex_transaction(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Parse individual Amex transaction"""
        try:
            # Parse date (format: "03 Aug 2025")
            date_str = row.get('Date', '').strip()
            if not date_str:
                return None
            
            transaction_date = datetime.strptime(date_str, '%d %b %Y').date()
            
            # Parse description
            description = row.get('Description', '').strip()
            if not description:
                description = 'Unknown Transaction'
            
            # Skip payment received transactions
            if 'PAYMENT RECEIVED' in description.upper():
                return None
            
            # Parse amount (Amex amounts are typically negative for charges/refunds)
            amount_str = row.get('Amount', '').strip()
            amount, direction = self._parse_amex_amount(amount_str, description)
            
            return {
                'item': description,
                'transaction_date': transaction_date,
                'amount': amount,
                'direction': direction
            }
        except Exception as e:
            logger.warning(f"Error parsing Amex transaction: {e}")
            return None
    
    def _parse_amex_amount(self, amount_str: str, description: str) -> Tuple[Decimal, str]:
        """Parse Amex amount string and determine direction"""
        if not amount_str or amount_str.strip() == '':
            return Decimal('0.00'), 'IN'
        
        # Remove common currency symbols and whitespace
        cleaned = amount_str.strip().replace('$', '').replace(',', '').replace('(', '').replace(')', '')
        
        # Check if it's negative (indicating a charge/refund transaction)
        is_negative = cleaned.startswith('-')
        
        # Remove negative sign
        if is_negative:
            cleaned = cleaned.replace('-', '')
        
        try:
            amount = Decimal(cleaned)
            
            # Determine direction based on description and amount
            # For Amex credit cards:
            # - Negative amounts are typically charges (OUT) 
            # - But some negative amounts can be refunds (IN) - need to check description
            # - Positive amounts are typically charges (OUT) - this is the key insight!
            
            # Check if this is a refund (negative amount that should be IN)
            if is_negative:
                # Look for refund indicators in description
                # WEB QP typically indicates a refund/credit
                refund_keywords = ['REFUND', 'CREDIT', 'ADJUSTMENT', 'REVERSAL', 'RETURN']
                is_refund = any(keyword in description.upper() for keyword in refund_keywords) or 'WEB QP' in description.upper()
                
                if is_refund:
                    direction = 'IN'  # Refund - money coming back to you
                else:
                    direction = 'OUT'  # Charge - money going out
            else:
                direction = 'OUT'  # Positive amount is typically a charge (money going out)
            
            return amount, direction
        except (ValueError, decimal.InvalidOperation):
            logger.warning(f"Could not parse Amex amount: {amount_str}")
            return Decimal('0.00'), 'IN'
