"""
Excel statement parser for bank statements
"""

import pandas as pd
import io
from datetime import datetime
from typing import List, Dict, Any, Tuple
import logging

from .base import BaseStatementParser

logger = logging.getLogger(__name__)


class ExcelStatementParser(BaseStatementParser):
    """Parser for Excel bank statements"""
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls']
    
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        return filename.lower().endswith(('.xlsx', '.xls'))
    
    def parse(self, file_content: bytes, filename: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        try:
            # Read Excel file
            df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise ValueError(f"Could not read Excel file: {e}")
        
        if df.empty:
            raise ValueError("Excel file is empty or has no data")
        
        # Extract statement metadata
        statement_meta = self._extract_statement_meta(filename, df)
        
        # Parse transaction details
        transactions = []
        for _, row in df.iterrows():
            transaction = self._parse_transaction_row(row)
            if transaction:
                transactions.append(transaction)
        
        return statement_meta, transactions
    
    def _extract_statement_meta(self, filename: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract statement metadata from filename and dataframe"""
        meta = {
            'bank_name': 'Unknown Bank',
            'account_number': 'Unknown',
            'account_abbr': 'Unknown',
            'statement_from_date': datetime.now().date(),
            'statement_to_date': datetime.now().date(),
            'statement_type': 'EXCEL'
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
        
        # Try to find date columns and extract date range
        date_columns = [col for col in df.columns if 'date' in str(col).lower()]
        if date_columns:
            dates = []
            for col in date_columns:
                for date_val in df[col].dropna():
                    try:
                        if pd.notna(date_val):
                            if isinstance(date_val, str):
                                parsed_date = self._parse_date(date_val)
                            else:
                                parsed_date = pd.to_datetime(date_val).date()
                            dates.append(parsed_date)
                    except:
                        continue
            
            if dates:
                dates.sort()
                meta['statement_from_date'] = dates[0]
                meta['statement_to_date'] = dates[-1]
        
        return meta
    
    def _parse_transaction_row(self, row: pd.Series) -> Dict[str, Any]:
        """Parse a single transaction row"""
        # Find columns by name patterns
        date_col = None
        desc_col = None
        amount_col = None
        
        for col in row.index:
            col_str = str(col).lower()
            if 'date' in col_str:
                date_col = col
            elif any(word in col_str for word in ['description', 'item', 'transaction', 'memo', 'payee']):
                desc_col = col
            elif any(word in col_str for word in ['amount', 'debit', 'credit', 'transaction']):
                amount_col = col
        
        if date_col is None or amount_col is None:
            return None
        
        # Parse the data
        try:
            transaction_date = self._parse_date(str(row[date_col]))
            item = str(row.get(desc_col, 'Unknown Transaction')) if desc_col else 'Unknown Transaction'
            amount, direction = self._parse_amount(str(row[amount_col]))
            
            return {
                'item': item,
                'transaction_date': transaction_date,
                'amount': amount,
                'direction': direction
            }
        except Exception as e:
            logger.warning(f"Error parsing row: {e}")
            return None
