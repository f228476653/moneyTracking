"""
CSV statement parser for bank statements
"""

import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Tuple

from .base import BaseStatementParser


class CSVStatementParser(BaseStatementParser):
    """Parser for CSV bank statements"""
    
    def __init__(self):
        self.supported_formats = ['.csv']
    
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        return filename.lower().endswith('.csv')
    
    def parse(self, file_content: bytes, filename: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
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
        
        # Extract statement metadata from first row or filename
        statement_meta = self._extract_statement_meta(filename, rows[0])
        
        # Parse transaction details
        transactions = []
        for row in rows:
            transaction = self._parse_transaction_row(row)
            if transaction:
                transactions.append(transaction)
        
        return statement_meta, transactions
    
    def _extract_statement_meta(self, filename: str, first_row: Dict[str, str]) -> Dict[str, Any]:
        """Extract statement metadata from filename and first row"""
        # Default values
        meta = {
            'bank_name': 'Unknown Bank',
            'account_number': 'Unknown',
            'account_abbr': 'Unknown',
            'statement_from_date': datetime.now().date(),
            'statement_to_date': datetime.now().date(),
            'statement_type': 'CSV'
        }
        
        # Try to extract bank name from filename
        filename_lower = filename.lower()
        if 'chase' in filename_lower:
            meta['bank_name'] = 'Chase Bank'
        elif 'wells' in filename_lower or 'fargo' in filename_lower:
            meta['bank_name'] = 'Wells Fargo'
        elif 'bank' in filename_lower or 'of america' in filename_lower:
            meta['bank_name'] = 'Bank of America'
        elif 'citibank' in filename_lower:
            meta['bank_name'] = 'Citibank'
        
        # Try to extract dates from column names or data
        date_columns = [col for col in first_row.keys() if 'date' in col.lower()]
        if date_columns:
            dates = []
            for col in date_columns:
                if first_row[col]:
                    try:
                        dates.append(self._parse_date(first_row[col]))
                    except:
                        continue
            
            if len(dates) >= 2:
                dates.sort()
                meta['statement_from_date'] = dates[0]
                meta['statement_to_date'] = dates[-1]
        
        return meta
    
    def _parse_transaction_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Parse a single transaction row"""
        # Common column name mappings
        column_mappings = {
            'date': ['date', 'transaction_date', 'post_date', 'posting_date'],
            'description': ['description', 'item', 'transaction', 'memo', 'payee'],
            'amount': ['amount', 'debit', 'credit', 'transaction_amount']
        }
        
        # Find the actual column names
        date_col = self._find_column(row, column_mappings['date'])
        desc_col = self._find_column(row, column_mappings['description'])
        amount_col = self._find_column(row, column_mappings['amount'])
        
        if not date_col or not amount_col:
            return None
        
        # Parse the data
        transaction_date = self._parse_date(row[date_col])
        item = row.get(desc_col, 'Unknown Transaction') if desc_col else 'Unknown Transaction'
        amount, direction = self._parse_amount(row[amount_col])
        
        return {
            'item': item,
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
