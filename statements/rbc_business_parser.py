"""
RBC Business Bank Account statement parser
"""

import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Tuple
from decimal import Decimal

from .base import BaseStatementParser


class RBCBusinessParser(BaseStatementParser):
    """Parser for RBC Business Bank Account CSV statements"""
    
    def __init__(self):
        self.supported_formats = ['.csv']
        self.expected_columns = [
            'Account Type', 'Account Number', 'Transaction Date', 'Cheque Number',
            'Description 1', 'Description 2', 'CAD$', 'USD$'
        ]
    
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        """Check if this is an RBC Business CSV file"""
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
        
        # Check if the CSV has the expected RBC Business columns
        try:
            csv_reader = csv.DictReader(io.StringIO(content))
            headers = csv_reader.fieldnames
            
            if not headers:
                return False
            
            # Check if all expected columns are present (case-insensitive)
            header_lower = [h.lower().strip() for h in headers]
            expected_lower = [h.lower().strip() for h in self.expected_columns]
            
            # Check if at least 6 out of 8 expected columns are present
            matches = sum(1 for expected in expected_lower if expected in header_lower)
            return matches >= 6
            
        except Exception:
            return False
    
    def parse(self, file_content: bytes, filename: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Parse the RBC Business CSV file"""
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
            'bank_name': 'RBC Business Banking',
            'account_number': 'Unknown',
            'account_abbr': 'RBC Business',
            'statement_from_date': datetime.now().date(),
            'statement_to_date': datetime.now().date(),
            'statement_type': 'RBC Business CSV'
        }
        
        # Extract account number from first row if available
        if rows and 'Account Number' in rows[0]:
            account_num = rows[0]['Account Number']
            if account_num and account_num.strip():
                meta['account_number'] = account_num.strip()
                # Create account abbreviation from account number
                meta['account_abbr'] = f"RBC-{account_num.split('-')[-1] if '-' in account_num else account_num[-4:]}"
        
        # Extract date range from transaction dates
        dates = []
        for row in rows:
            if 'Transaction Date' in row and row['Transaction Date']:
                try:
                    date_obj = self._parse_date(row['Transaction Date'])
                    dates.append(date_obj)
                except:
                    continue
        
        if dates:
            dates.sort()
            meta['statement_from_date'] = dates[0]
            meta['statement_to_date'] = dates[-1]
        
        return meta
    
    def _parse_transaction_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Parse a single RBC Business transaction row"""
        # Get transaction date
        transaction_date = None
        if 'Transaction Date' in row and row['Transaction Date']:
            try:
                transaction_date = self._parse_date(row['Transaction Date'])
            except:
                transaction_date = datetime.now().date()
        else:
            return None  # Skip rows without dates
        
        # Build description from Description 1 and Description 2
        description_parts = []
        if 'Description 1' in row and row['Description 1']:
            description_parts.append(row['Description 1'].strip())
        if 'Description 2' in row and row['Description 2']:
            description_parts.append(row['Description 2'].strip())
        
        item = ' '.join(description_parts) if description_parts else 'Unknown Transaction'
        
        # Determine amount and direction
        amount = Decimal('0.00')
        direction = 'IN'
        
        # Check CAD$ first (primary currency)
        if 'CAD$' in row and row['CAD$']:
            cad_amount = row['CAD$'].strip()
            if cad_amount:
                amount, direction = self._parse_amount(cad_amount)
        # Fallback to USD$ if CAD$ is empty
        elif 'USD$' in row and row['USD$']:
            usd_amount = row['USD$'].strip()
            if usd_amount:
                amount, direction = self._parse_amount(usd_amount)
        
        # Skip transactions with zero amount
        if amount == Decimal('0.00'):
            return None
        
        return {
            'item': item,
            'transaction_date': transaction_date,
            'amount': amount,
            'direction': direction
        }
    
    def _parse_amount(self, amount_str: str) -> Tuple[Decimal, str]:
        """Parse amount string and determine direction (IN/OUT) for RBC format"""
        if not amount_str or amount_str.strip() == '':
            return Decimal('0.00'), 'IN'
        
        # Remove common currency symbols and whitespace
        cleaned = amount_str.strip().replace('$', '').replace(',', '').replace('(', '').replace(')', '')
        
        # Check if it's negative (indicating OUT)
        is_negative = cleaned.startswith('-')
        
        # Remove negative sign
        if is_negative:
            cleaned = cleaned.replace('-', '')
        
        try:
            amount = Decimal(cleaned)
            direction = 'OUT' if is_negative else 'IN'
            return amount, direction
        except (ValueError, Exception):
            return Decimal('0.00'), 'IN'
