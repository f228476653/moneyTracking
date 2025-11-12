"""
Tests for the statement parser factory
"""

from django.test import TestCase

from ..factory import StatementParserFactory
from ..amex_parser import AmexCreditCardParser
from ..csv_parser import CSVStatementParser
from ..exceptions import ParserNotFoundError


class StatementParserFactoryTest(TestCase):
    """Test cases for StatementParserFactory"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = StatementParserFactory()

    def test_get_parser_amex(self):
        """Test getting Amex parser"""
        csv_content = b"""Date,Date Processed,Description,Card Member,Account #,Amount
15 Jan 2025,16 Jan 2025,GROCERY STORE,JOHN DOE,*****1234,-100.00
"""
        parser = self.factory.get_parser(csv_content, 'statement.csv')
        self.assertIsInstance(parser, AmexCreditCardParser)

    def test_get_parser_generic_csv(self):
        """Test getting generic CSV parser for non-Amex CSV"""
        csv_content = b"""Date,Transaction,Amount
2025-01-15,Purchase,100.00
"""
        parser = self.factory.get_parser(csv_content, 'statement.csv')
        self.assertIsInstance(parser, CSVStatementParser)

    def test_get_parser_no_match_raises_error(self):
        """Test that no matching parser raises ValueError"""
        # Create content that no parser can handle
        invalid_content = b'\x00\x01\x02\x03'  # Binary garbage
        with self.assertRaises(ValueError) as context:
            self.factory.get_parser(invalid_content, 'unknown.xyz')
        self.assertIn('No parser found', str(context.exception))

    def test_parse_statement_success(self):
        """Test successful statement parsing through factory"""
        csv_content = b"""Date,Date Processed,Description,Card Member,Account #,Amount
15 Jan 2025,16 Jan 2025,GROCERY STORE,JOHN DOE,*****1234,-100.00
"""
        statement_meta, transactions = self.factory.parse_statement(csv_content, 'amex.csv')

        self.assertEqual(statement_meta['bank_name'], 'American Express')
        self.assertEqual(len(transactions), 1)

    def test_parser_priority_order(self):
        """Test that parsers are checked in the correct priority order"""
        # Verify that specialized parsers come before generic ones
        parser_classes = [type(p).__name__ for p in self.factory.parsers]

        # Amex should come before generic CSV
        amex_index = parser_classes.index('AmexCreditCardParser')
        csv_index = parser_classes.index('CSVStatementParser')
        self.assertLess(amex_index, csv_index, "Amex parser should have higher priority than generic CSV")

        # Wealthsimple PDF should come first
        self.assertEqual(parser_classes[0], 'WealthsimpleRRSPParser')
