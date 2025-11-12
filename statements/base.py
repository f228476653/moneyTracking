"""
Base parser class and common utilities for bank statement parsing
"""

import pandas as pd
from datetime import datetime
import decimal
from decimal import Decimal
from typing import List, Dict, Any, Tuple, Optional
import logging

from .constants import COMMON_DATE_FORMATS, DIRECTION_IN, DIRECTION_OUT
from .exceptions import DateParsingError, AmountParsingError

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
        """
        Parse amount string and determine direction (IN/OUT).

        Args:
            amount_str: String representation of the amount

        Returns:
            Tuple of (Decimal amount, direction string)

        Raises:
            AmountParsingError: If amount cannot be parsed after cleaning
        """
        if not amount_str or amount_str.strip() == '':
            return Decimal('0.00'), DIRECTION_IN

        # Remove common currency symbols and whitespace
        cleaned = amount_str.strip().replace('$', '').replace(',', '').replace('(', '').replace(')', '')

        # Check if it's negative or in parentheses (indicating OUT)
        is_negative = cleaned.startswith('-') or cleaned.startswith('(')

        # Remove negative sign or parentheses
        if is_negative:
            cleaned = cleaned.replace('-', '').replace('(', '').replace(')', '')

        try:
            amount = Decimal(cleaned)
            direction = DIRECTION_OUT if is_negative else DIRECTION_IN
            return amount, direction
        except (ValueError, decimal.InvalidOperation) as e:
            logger.error(f"Could not parse amount: {amount_str}", exc_info=True)
            raise AmountParsingError(f"Failed to parse amount: {amount_str}") from e
    
    def _parse_date(self, date_str: str) -> datetime.date:
        """
        Parse date string into date object.

        Args:
            date_str: String representation of the date

        Returns:
            datetime.date object

        Raises:
            DateParsingError: If date cannot be parsed with any known format
        """
        if not date_str or date_str.strip() == '':
            logger.warning("Empty date string provided, using current date")
            return datetime.now().date()

        # Try common date formats
        for fmt in COMMON_DATE_FORMATS:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        # If none of the formats work, try pandas parsing
        try:
            return pd.to_datetime(date_str).date()
        except Exception as e:
            logger.error(f"Could not parse date: {date_str}", exc_info=True)
            raise DateParsingError(f"Failed to parse date: {date_str}") from e
