"""
Tests for the Amex credit card parser
"""

from django.test import TestCase
from decimal import Decimal
from datetime import datetime

from ..amex_parser import AmexCreditCardParser


class AmexCreditCardParserTest(TestCase):
    """Test cases for AmexCreditCardParser"""

    def setUp(self):
        """Set up test fixtures"""
        self.parser = AmexCreditCardParser()

    def test_can_parse_valid_amex_csv(self):
        """Test that parser recognizes valid Amex CSV"""
        csv_content = b"""Date,Date Processed,Description,Card Member,Account #,Amount
15 Jan 2025,16 Jan 2025,GROCERY STORE,JOHN DOE,*****1234,-100.00
"""
        self.assertTrue(self.parser.can_parse(csv_content, 'statement.csv'))

    def test_can_parse_invalid_file_extension(self):
        """Test that parser rejects non-CSV files"""
        self.assertFalse(self.parser.can_parse(b'data', 'statement.pdf'))

    def test_can_parse_invalid_headers(self):
        """Test that parser rejects CSV with wrong headers"""
        csv_content = b"""Transaction Date,Description,Amount
15 Jan 2025,GROCERY STORE,100.00
"""
        self.assertFalse(self.parser.can_parse(csv_content, 'statement.csv'))

    def test_parse_valid_amex_statement(self):
        """Test parsing a valid Amex statement"""
        csv_content = b"""Date,Date Processed,Description,Card Member,Account #,Amount
15 Jan 2025,16 Jan 2025,GROCERY STORE,JOHN DOE,*****1234,-100.00
20 Jan 2025,21 Jan 2025,REFUND FROM STORE,JOHN DOE,*****1234,50.00
"""
        statement_meta, transactions = self.parser.parse(csv_content, 'amex_jan2025.csv')

        # Check statement metadata
        self.assertEqual(statement_meta['bank_name'], 'American Express')
        self.assertEqual(statement_meta['account_abbr'], 'AMEX')
        self.assertEqual(statement_meta['statement_type'], 'CSV')

        # Check transactions
        self.assertEqual(len(transactions), 2)

        # First transaction (charge)
        self.assertEqual(transactions[0]['item'], 'GROCERY STORE')
        self.assertEqual(transactions[0]['amount'], Decimal('100.00'))
        self.assertEqual(transactions[0]['direction'], 'IN')

        # Second transaction (refund - positive amount)
        self.assertEqual(transactions[1]['item'], 'REFUND FROM STORE')
        self.assertEqual(transactions[1]['amount'], Decimal('50.00'))
        self.assertEqual(transactions[1]['direction'], 'OUT')

    def test_parse_amex_amount_negative(self):
        """Test parsing negative Amex amount (refund)"""
        amount, direction = self.parser._parse_amex_amount('-100.00', 'STORE REFUND')
        self.assertEqual(amount, Decimal('100.00'))
        self.assertEqual(direction, 'IN')

    def test_parse_amex_amount_positive(self):
        """Test parsing positive Amex amount (charge)"""
        amount, direction = self.parser._parse_amex_amount('100.00', 'GROCERY STORE')
        self.assertEqual(amount, Decimal('100.00'))
        self.assertEqual(direction, 'OUT')

    def test_parse_amex_amount_payment_received(self):
        """Test that PAYMENT RECEIVED is skipped"""
        csv_content = b"""Date,Date Processed,Description,Card Member,Account #,Amount
15 Jan 2025,16 Jan 2025,PAYMENT RECEIVED,JOHN DOE,*****1234,-500.00
20 Jan 2025,21 Jan 2025,GROCERY STORE,JOHN DOE,*****1234,-100.00
"""
        statement_meta, transactions = self.parser.parse(csv_content, 'amex_jan2025.csv')

        # PAYMENT RECEIVED should be skipped
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]['item'], 'GROCERY STORE')

    def test_extract_account_info(self):
        """Test extracting account information from CSV"""
        csv_content = """Date,Date Processed,Description,Card Member,Account #,Amount
15 Jan 2025,16 Jan 2025,GROCERY STORE,JOHN DOE,*****1234,-100.00
"""
        account_info = self.parser._extract_account_info(csv_content)
        self.assertEqual(account_info['account_number'], '*****1234')

    def test_parse_empty_csv(self):
        """Test parsing CSV with only headers"""
        csv_content = b"""Date,Date Processed,Description,Card Member,Account #,Amount
"""
        statement_meta, transactions = self.parser.parse(csv_content, 'empty.csv')
        self.assertEqual(len(transactions), 0)
