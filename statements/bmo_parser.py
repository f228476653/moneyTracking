"""
BMO Bank Account statement parser for CSV statements
"""

import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Tuple
from decimal import Decimal

from .base import BaseStatementParser


class BMOBankParser(BaseStatementParser):
    """Parser for BMO Bank Account CSV statements"""
    
    def __init__(self):
        self.supported_formats = ['.csv']
        self.expected_columns = [
            'First Bank Card', 'Transaction Type', 'Date Posted', 'Transaction Amount', 'Description'
        ]
    
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        """Check if this is a BMO Bank CSV file"""
        if not filename.lower().endswith('.csv'):
            return False
        
        try:
            # Try to decode as UTF-8 first
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to other encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    content = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return False
        
        # Check if the CSV has the expected BMO columns
        try:
            csv_reader = csv.DictReader(io.StringIO(content))
            headers = csv_reader.fieldnames
            
            if not headers:
                return False
            
            # Check if all expected columns are present (case-insensitive)
            header_lower = [h.lower().strip() for h in headers]
            expected_lower = [h.lower().strip() for h in self.expected_columns]
            
            # Check if all 5 expected columns are present
            matches = sum(1 for expected in expected_lower if expected in header_lower)
            return matches == 5
            
        except Exception:
            return False
    
    def parse(self, file_content: bytes, filename: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Parse the BMO Bank CSV file"""
        try:
            # Try to decode as UTF-8 first
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to other encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    content = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode CSV file")
        
        # Parse CSV content
        csv_reader = csv.DictReader(io.StringIO(content))
        rows = list(csv_reader)
        
        if not rows:
            raise ValueError("CSV file is empty or has no data rows")
        
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
        # Default values
        meta = {
            'bank_name': 'BMO Bank of Montreal',
            'account_number': 'Unknown',
            'account_abbr': 'BMO',
            'statement_from_date': datetime.now().date(),
            'statement_to_date': datetime.now().date(),
            'statement_type': 'BMO Bank CSV'
        }
        
        # Extract account number from first row if available
        if rows and 'First Bank Card' in rows[0]:
            account_num = rows[0]['First Bank Card']
            if account_num and account_num.strip():
                # Remove quotes if present
                account_num = account_num.strip().strip("'\"")
                meta['account_number'] = account_num
                # Create account abbreviation from last 4 digits
                meta['account_abbr'] = f"BMO-{account_num[-4:]}"
        
        # Extract date range from transaction dates
        dates = []
        for row in rows:
            if 'Date Posted' in row and row['Date Posted']:
                try:
                    date_obj = self._parse_date(row['Date Posted'])
                    dates.append(date_obj)
                except:
                    continue
        
        if dates:
            dates.sort()
            meta['statement_from_date'] = dates[0]
            meta['statement_to_date'] = dates[-1]
        
        return meta
    
    def _parse_transaction_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Parse a single BMO Bank transaction row"""
        # Get transaction date
        transaction_date = None
        if 'Date Posted' in row and row['Date Posted']:
            try:
                transaction_date = self._parse_date(row['Date Posted'])
            except:
                transaction_date = datetime.now().date()
        else:
            return None  # Skip rows without dates
        
        # Get description
        item = 'Unknown Transaction'
        if 'Description' in row and row['Description']:
            item = row['Description'].strip()
        
        # Get transaction type and amount
        transaction_type = row.get('Transaction Type', '').strip()
        # Handle both 'Transaction Amount' and ' Transaction Amount' (with leading space)
        amount_str = row.get('Transaction Amount', '').strip() or row.get(' Transaction Amount', '').strip()
        
        # Parse amount and determine direction
        amount = Decimal('0.00')
        direction = 'IN'
        
        if amount_str:
            try:
                # Remove quotes if present
                amount_str = amount_str.strip().strip("'\"")
                amount = Decimal(amount_str)
                
                # Determine direction based on transaction type and amount
                if transaction_type.upper() == 'DEBIT' or amount < 0:
                    direction = 'OUT'
                    amount = abs(amount)  # Store as positive value
                elif transaction_type.upper() == 'CREDIT' or amount > 0:
                    direction = 'IN'
                else:
                    # Fallback: negative amount means OUT
                    if amount < 0:
                        direction = 'OUT'
                        amount = abs(amount)
                    else:
                        direction = 'IN'
            except (ValueError, Exception):
                return None  # Skip invalid amount rows
        
        # Skip transactions with zero amount
        if amount == Decimal('0.00'):
            return None
        
        return {
            'item': item,
            'transaction_date': transaction_date,
            'amount': amount,
            'direction': direction
        }
    
    def _parse_date(self, date_str: str) -> datetime.date:
        """Parse BMO date format (YYYYMMDD)"""
        if not date_str or date_str.strip() == '':
            return datetime.now().date()
        
        # Remove quotes if present
        date_str = date_str.strip().strip("'\"")
        
        # BMO format is YYYYMMDD
        try:
            return datetime.strptime(date_str, '%Y%m%d').date()
        except ValueError:
            # Fallback to base class method
            return super()._parse_date(date_str)
