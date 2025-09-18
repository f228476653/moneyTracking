"""
EQ Joint account parser for bank statements
"""

import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Tuple

from .base import BaseStatementParser


class EQJointParser(BaseStatementParser):
    """Parser for EQ Joint account statements"""
    
    def __init__(self):
        self.supported_formats = ['.csv']
    
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        """Check if this is an EQ Joint statement"""
        if not filename.lower().endswith('.csv'):
            return False
        
        try:
            # Try to decode and check the content
            content = file_content.decode('utf-8')
            lines = content.strip().split('\n')
            
            if len(lines) < 2:
                return False
            
            # Check if the header matches EQ Joint format (more flexible)
            header = lines[0].strip().lower()
            
            # Check for common column name variations
            date_columns = ['transfer date', 'date', 'transaction date']
            desc_columns = ['description', 'desc', 'item', 'transaction']
            amount_columns = ['amount', 'transaction amount']
            balance_columns = ['balance', 'running balance', 'account balance']
            
            has_date = any(col in header for col in date_columns)
            has_desc = any(col in header for col in desc_columns)
            has_amount = any(col in header for col in amount_columns)
            has_balance = any(col in header for col in balance_columns)
            
            # Need at least date, description, and amount columns
            if not (has_date and has_desc and has_amount):
                return False
            
            # Check if there's at least one data row with EQ Joint characteristics
            for line in lines[1:3]:  # Check first few data rows
                if line.strip():
                    # Look for EQ Joint specific patterns
                    if any(keyword in line.lower() for keyword in ['interest received', 'auto-withdrawal', 'ws investments', 'eq bank']):
                        return True
            
            return False
            
        except (UnicodeDecodeError, Exception):
            return False
    
    def parse(self, file_content: bytes, filename: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Parse the EQ Joint statement"""
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
                raise ValueError("Could not decode EQ Joint CSV file")
        
        # Parse CSV content
        csv_reader = csv.DictReader(io.StringIO(content))
        rows = list(csv_reader)
        
        if not rows:
            raise ValueError("EQ Joint CSV file is empty or has no data rows")
        
        # Extract statement metadata
        statement_meta = self._extract_statement_meta(filename, rows)
        
        # Parse transaction details
        transactions = []
        for row in rows:
            transaction = self._parse_transaction_row(row)
            if transaction:
                transactions.append(transaction)
        
        return statement_meta, transactions
    
    def _extract_statement_meta(self, filename: str, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        """Extract statement metadata from filename and data"""
        meta = {
            'bank_name': 'EQ Bank',
            'account_number': 'EQ Joint',
            'account_abbr': 'EQ_JOINT',
            'statement_from_date': datetime.now().date(),
            'statement_to_date': datetime.now().date(),
            'statement_type': 'CSV'
        }
        
        # Extract dates from transaction data
        dates = []
        for row in rows:
            if row.get('Transfer Date'):
                try:
                    date_obj = self._parse_eq_date(row['Transfer Date'])
                    dates.append(date_obj)
                except:
                    continue
        
        if dates:
            dates.sort()
            meta['statement_from_date'] = dates[0]
            meta['statement_to_date'] = dates[-1]
        
        return meta
    
    def _parse_transaction_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Parse a single EQ Joint transaction row"""
        # Find the correct column names (case-insensitive)
        date_col = self._find_column(row, ['Transfer Date', 'Date', 'Transaction Date'])
        desc_col = self._find_column(row, ['Description', 'Desc', 'Item', 'Transaction'])
        amount_col = self._find_column(row, ['Amount', 'Transaction Amount'])
        balance_col = self._find_column(row, ['Balance', 'Running Balance', 'Account Balance'])
        
        if not date_col or not amount_col:
            return None
        
        # Get the data from the found columns
        transfer_date = row.get(date_col, '').strip()
        description = row.get(desc_col, '').strip() if desc_col else 'Unknown Transaction'
        amount_str = row.get(amount_col, '').strip()
        
        if not transfer_date or not amount_str:
            return None
        
        # Parse the date using EQ Joint specific format
        try:
            transaction_date = self._parse_eq_date(transfer_date)
        except:
            return None
        
        # Parse amount and determine direction
        amount, direction = self._parse_amount(amount_str)
        
        return {
            'item': description,
            'transaction_date': transaction_date,
            'amount': amount,
            'direction': direction
        }
    
    def _find_column(self, row: Dict[str, str], possible_names: List[str]) -> str:
        """Find a column by trying different possible names (case-insensitive)"""
        for name in possible_names:
            # Try exact match first
            if name in row:
                return name
            # Try case-insensitive match
            for col_name in row.keys():
                if col_name.lower() == name.lower():
                    return col_name
        return None
    
    def _parse_eq_date(self, date_str: str) -> datetime.date:
        """Parse EQ Joint specific date format: '01 MAY 2025'"""
        if not date_str or date_str.strip() == '':
            return datetime.now().date()
        
        # EQ Joint format: "01 MAY 2025"
        try:
            return datetime.strptime(date_str.strip(), '%d %b %Y').date()
        except ValueError:
            # Try other common formats as fallback
            return self._parse_date(date_str)
