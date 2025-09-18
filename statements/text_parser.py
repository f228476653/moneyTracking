"""
Text statement parser for bank statements
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Tuple

from .base import BaseStatementParser


class TextStatementParser(BaseStatementParser):
    """Parser for text-based bank statements"""
    
    def __init__(self):
        self.supported_formats = ['.txt', '.log']
    
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        return filename.lower().endswith(('.txt', '.log'))
    
    def parse(self, file_content: bytes, filename: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        try:
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = file_content.decode('latin-1')
            except UnicodeDecodeError:
                raise ValueError("Could not decode text file")
        
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
        """Extract statement metadata from filename and lines"""
        meta = {
            'bank_name': 'Unknown Bank',
            'account_number': 'Unknown',
            'account_abbr': 'Unknown',
            'statement_from_date': datetime.now().date(),
            'statement_to_date': datetime.now().date(),
            'statement_type': 'TXT'
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
        
        return meta
    
    def _parse_transaction_line(self, line: str) -> Dict[str, Any]:
        """Parse a single transaction line"""
        # Simple parsing for common formats
        parts = line.strip().split()
        if len(parts) < 3:
            return None
        
        try:
            # Try to find date, amount, and description
            for i, part in enumerate(parts):
                # Look for date pattern
                if self._looks_like_date(part):
                    date_str = part
                    # Look for amount pattern
                    amount_str = None
                    for j, amount_part in enumerate(parts):
                        if self._looks_like_amount(amount_part):
                            amount_str = amount_part
                            # Everything else is description
                            desc_parts = [p for k, p in enumerate(parts) if k != i and k != j]
                            description = ' '.join(desc_parts)
                            break
                    
                    if amount_str:
                        amount, direction = self._parse_amount(amount_str)
                        return {
                            'item': description or 'Unknown Transaction',
                            'transaction_date': self._parse_date(date_str),
                            'amount': amount,
                            'direction': direction
                        }
        except:
            pass
        
        return None
    
    def _looks_like_date(self, text: str) -> bool:
        """Check if text looks like a date"""
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, text):
                return True
        return False
    
    def _looks_like_amount(self, text: str) -> bool:
        """Check if text looks like an amount"""
        amount_patterns = [
            r'^\$?\d+\.\d{2}$',  # $123.45 or 123.45
            r'^\$?\d+,\d{3}\.\d{2}$',  # $1,234.56
            r'^\(\$?\d+\.\d{2}\)$',  # ($123.45)
        ]
        
        for pattern in amount_patterns:
            if re.match(pattern, text):
                return True
        return False
