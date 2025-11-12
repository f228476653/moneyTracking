"""
Tests for the base parser class
"""

from django.test import TestCase
from decimal import Decimal
from datetime import datetime

from ..base import BaseStatementParser
from ..exceptions import AmountParsingError, DateParsingError
from ..constants import DIRECTION_IN, DIRECTION_OUT


class BaseStatementParserTest(TestCase):
    """Test cases for BaseStatementParser"""

    def setUp(self):
        """Set up test fixtures"""
        self.parser = BaseStatementParser()

    def test_parse_amount_positive(self):
        """Test parsing positive amount"""
        amount, direction = self.parser._parse_amount('100.50')
        self.assertEqual(amount, Decimal('100.50'))
        self.assertEqual(direction, DIRECTION_IN)

    def test_parse_amount_negative(self):
        """Test parsing negative amount"""
        amount, direction = self.parser._parse_amount('-50.25')
        self.assertEqual(amount, Decimal('50.25'))
        self.assertEqual(direction, DIRECTION_OUT)

    def test_parse_amount_with_dollar_sign(self):
        """Test parsing amount with dollar sign"""
        amount, direction = self.parser._parse_amount('$1,234.56')
        self.assertEqual(amount, Decimal('1234.56'))
        self.assertEqual(direction, DIRECTION_IN)

    def test_parse_amount_with_parentheses(self):
        """Test parsing amount with parentheses (negative)"""
        amount, direction = self.parser._parse_amount('(250.00)')
        self.assertEqual(amount, Decimal('250.00'))
        self.assertEqual(direction, DIRECTION_OUT)

    def test_parse_amount_empty_string(self):
        """Test parsing empty amount string"""
        amount, direction = self.parser._parse_amount('')
        self.assertEqual(amount, Decimal('0.00'))
        self.assertEqual(direction, DIRECTION_IN)

    def test_parse_amount_invalid_raises_exception(self):
        """Test that invalid amount raises AmountParsingError"""
        with self.assertRaises(AmountParsingError):
            self.parser._parse_amount('invalid')

    def test_parse_date_iso_format(self):
        """Test parsing date in ISO format"""
        date = self.parser._parse_date('2025-01-15')
        self.assertEqual(date, datetime(2025, 1, 15).date())

    def test_parse_date_us_format(self):
        """Test parsing date in US format"""
        date = self.parser._parse_date('01/15/2025')
        self.assertEqual(date, datetime(2025, 1, 15).date())

    def test_parse_date_amex_format(self):
        """Test parsing date in Amex format"""
        date = self.parser._parse_date('15 Jan 2025')
        self.assertEqual(date, datetime(2025, 1, 15).date())

    def test_parse_date_empty_string(self):
        """Test parsing empty date string returns today"""
        date = self.parser._parse_date('')
        self.assertEqual(date, datetime.now().date())

    def test_parse_date_invalid_raises_exception(self):
        """Test that invalid date raises DateParsingError"""
        with self.assertRaises(DateParsingError):
            self.parser._parse_date('not-a-date-99/99/9999')

    def test_can_parse_not_implemented(self):
        """Test that can_parse raises NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            self.parser.can_parse(b'', 'test.csv')

    def test_parse_not_implemented(self):
        """Test that parse raises NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            self.parser.parse(b'', 'test.csv')
