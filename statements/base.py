"""
Base parser class and common utilities for bank statement parsing
"""

import pandas as pd
from datetime import datetime
import decimal
from decimal import Decimal
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class BaseStatementParser:
    """Base class for parsing bank statements"""
    
    def __init__(self):
        self.supported_formats = []
    
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        """Check if this parser can handle the given file"""
        raise NotImplementedError
    
    def parse(self, file_content: bytes, filename: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Parse the file and return statement metadata and transaction details"""
        raise NotImplementedError
    
    def _parse_amount(self, amount_str: str) -> Tuple[Decimal, str]:
        """Parse amount string and determine direction (IN/OUT)"""
        if not amount_str or amount_str.strip() == '':
            return Decimal('0.00'), 'IN'
        
        # Remove common currency symbols and whitespace
        cleaned = amount_str.strip().replace('$', '').replace(',', '').replace('(', '').replace(')', '')
        
        # Check if it's negative or in parentheses (indicating OUT)
        is_negative = cleaned.startswith('-') or cleaned.startswith('(')
        
        # Remove negative sign or parentheses
        if is_negative:
            cleaned = cleaned.replace('-', '').replace('(', '').replace(')', '')
        
        try:
            amount = Decimal(cleaned)
            direction = 'OUT' if is_negative else 'IN'
            return amount, direction
        except (ValueError, decimal.InvalidOperation):
            logger.warning(f"Could not parse amount: {amount_str}")
            return Decimal('0.00'), 'IN'
    
    def _parse_date(self, date_str: str) -> datetime.date:
        """Parse date string into date object"""
        if not date_str or date_str.strip() == '':
            return datetime.now().date()
        
        # Common date formats
        date_formats = [
            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
            '%m-%d-%Y', '%d-%m-%Y', '%b %d, %Y', '%B %d, %Y',
            '%d %b %Y', '%d %B %Y'  # Amex format: "03 Aug 2025"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        
        # If none of the formats work, try pandas parsing
        try:
            return pd.to_datetime(date_str).date()
        except:
            logger.warning(f"Could not parse date: {date_str}")
            return datetime.now().date()
