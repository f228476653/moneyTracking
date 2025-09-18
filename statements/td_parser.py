"""
TD Bank cheque account parser for CSV statements
"""

import csv
import re
from io import StringIO
from datetime import datetime
from typing import List, Dict, Any, Tuple
import logging
from decimal import Decimal
import decimal

from .base import BaseStatementParser

logger = logging.getLogger(__name__)


class TDChequeAccountParser(BaseStatementParser):
    """Parser specifically for TD Bank cheque account CSV files"""
    
    def __init__(self):
        self.supported_formats = ['.csv']
    
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        """Check if this is a TD cheque account CSV file"""
        if not filename.lower().endswith('.csv'):
            return False
        
        try:
            content = file_content.decode('utf-8')
            lines = content.split('\n')
            
            # Check for TD-specific format: date,description,amount,,balance
            if len(lines) > 0:
                first_line = lines[0].strip()
                # Use CSV reader to properly parse the line
                
                try:
                    csv_reader = csv.reader(StringIO(first_line))
                    parts = next(csv_reader)
                    
                    # TD format should have at least 3 parts: date, description, amount
                    if len(parts) >= 3:
                        date_part = parts[0].strip()
                        # Check if first field looks like a TD date (YYYY-MM-DD)
                        if self._looks_like_td_date(date_part):
                            return True
                except:
                    pass
        except:
            pass
        
        return False
    
    def parse(self, file_content: bytes, filename: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Parse TD cheque account CSV file"""
        try:
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            # Try other encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    content = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode TD CSV file")
        
        lines = content.split('\n')
        
        # Extract statement metadata
        statement_meta = self._extract_statement_meta(filename, lines)
        
        # Parse transaction details
        transactions = []
        for line in lines:
            if line.strip():
                transaction = self._parse_transaction_line(line)
                if transaction:
                    transactions.append(transaction)
        
        return statement_meta, transactions
    
    def _extract_statement_meta(self, filename: str, lines: List[str]) -> Dict[str, Any]:
        """Extract statement metadata from TD CSV file"""
        meta = {
            'bank_name': 'TD Bank',
            'account_number': 'Unknown',
            'account_abbr': 'TD-CHEQUE',
            'statement_from_date': datetime.now().date(),
            'statement_to_date': datetime.now().date(),
            'statement_type': 'TD-CSV'
        }
        
        # Extract date range from transaction dates
        dates = []
        for line in lines:
            if line.strip():
                transaction = self._parse_transaction_line(line)
                if transaction:
                    dates.append(transaction['transaction_date'])
        
        if dates:
            dates.sort()
            meta['statement_from_date'] = dates[0]
            meta['statement_to_date'] = dates[-1]
        
        return meta
    
    def _parse_transaction_line(self, line: str) -> Dict[str, Any]:
        """Parse a single TD transaction line"""
        try:
            # Use CSV reader to properly handle quoted fields
            # Create a CSV reader to properly parse quoted fields
            csv_reader = csv.reader(StringIO(line))
            parts = next(csv_reader)
            
            # TD format: date, description, amount_or_empty, amount_or_empty, balance
            if len(parts) >= 4:
                date_str = parts[0].strip()
                description = parts[1].strip()
                
                # Determine if this is IN or OUT transaction based on field positions
                field3 = parts[2].strip()
                field4 = parts[3].strip()
                
                # If field3 has a value and field4 is empty, it's an OUT transaction
                # If field3 is empty and field4 has a value, it's an IN transaction
                if field3 and not field4:
                    amount_str = field3
                    direction = 'OUT'
                elif not field3 and field4:
                    amount_str = field4
                    direction = 'IN'
                else:
                    # Fallback: try to determine based on which field has a value
                    if field3:
                        amount_str = field3
                        direction = 'OUT'
                    elif field4:
                        amount_str = field4
                        direction = 'IN'
                    else:
                        return None  # No amount found
                
                # Validate date format
                if not self._looks_like_td_date(date_str):
                    return None
                
                # Parse the data
                transaction_date = self._parse_date(date_str)
                item = description if description else 'Unknown Transaction'
                amount, _ = self._parse_td_amount(amount_str)  # Ignore direction from parser, use our logic
                
                return {
                    'item': item,
                    'transaction_date': transaction_date,
                    'amount': amount,
                    'direction': direction
                }
        except Exception as e:
            logger.warning(f"Error parsing TD transaction line: {e}")
        
        return None
    
    def _looks_like_td_date(self, text: str) -> bool:
        """Check if text looks like a TD date (YYYY-MM-DD)"""
        # TD uses YYYY-MM-DD format
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        return bool(re.match(pattern, text))
    
    def _parse_td_amount(self, amount_str: str) -> Tuple[Decimal, str]:
        """Parse TD amount string (direction is determined by field position)"""
        if not amount_str or amount_str.strip() == '':
            return Decimal('0.00'), 'IN'
        
        # Remove common currency symbols and whitespace
        cleaned = amount_str.strip().replace('$', '').replace(',', '')
        
        try:
            amount = Decimal(cleaned)
            # Direction is determined by field position, not by the amount itself
            # Just return a default direction (will be overridden by caller)
            return amount, 'IN'
        except (ValueError, decimal.InvalidOperation):
            logger.warning(f"Could not parse TD amount: {amount_str}")
            return Decimal('0.00'), 'IN'
