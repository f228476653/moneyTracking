"""
Tests for utility functions
"""

from django.test import TestCase
from decimal import Decimal
from datetime import date

from ..models import Account, Statement, StatementDetail
from ..utils import categorize_transaction, aggregate_transactions_by_category, is_payment_transaction
from ..constants import DIRECTION_IN, DIRECTION_OUT


class UtilsTest(TestCase):
    """Test cases for utility functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.account = Account.objects.create(
            account_abbr='TEST_CHQ',
            bank_name='Test Bank',
            account_number='12345678',
            account_type='BANK'
        )

        self.statement = Statement.objects.create(
            account=self.account,
            source_file='test_statement.csv',
            statement_from_date=date(2025, 1, 1),
            statement_to_date=date(2025, 1, 31),
            statement_type='CSV'
        )

    def test_categorize_transaction_transfer(self):
        """Test categorizing transfer transaction"""
        transaction = StatementDetail.objects.create(
            statement=self.statement,
            item='TRANSFER TO EQ BANK',
            transaction_date=date(2025, 1, 15),
            amount=Decimal('1000.00'),
            direction=DIRECTION_OUT
        )

        category = categorize_transaction(transaction)
        self.assertEqual(category, 'transfer')

    def test_categorize_transaction_investment(self):
        """Test categorizing investment transaction"""
        transaction = StatementDetail.objects.create(
            statement=self.statement,
            item='QUESTRADE INVESTMENT',
            transaction_date=date(2025, 1, 15),
            amount=Decimal('500.00'),
            direction=DIRECTION_OUT
        )

        category = categorize_transaction(transaction)
        self.assertEqual(category, 'investment')

    def test_categorize_transaction_spending(self):
        """Test categorizing spending transaction"""
        transaction = StatementDetail.objects.create(
            statement=self.statement,
            item='GROCERY STORE',
            transaction_date=date(2025, 1, 15),
            amount=Decimal('150.00'),
            direction=DIRECTION_OUT
        )

        category = categorize_transaction(transaction)
        self.assertEqual(category, 'spending')

    def test_categorize_transaction_income(self):
        """Test categorizing income transaction"""
        transaction = StatementDetail.objects.create(
            statement=self.statement,
            item='SALARY DEPOSIT',
            transaction_date=date(2025, 1, 15),
            amount=Decimal('2000.00'),
            direction=DIRECTION_IN
        )

        category = categorize_transaction(transaction)
        self.assertEqual(category, 'income')

    def test_categorize_transaction_gic_not_income(self):
        """Test that GIC is not categorized as income"""
        transaction = StatementDetail.objects.create(
            statement=self.statement,
            item='GIC PURCHASE',
            transaction_date=date(2025, 1, 15),
            amount=Decimal('5000.00'),
            direction=DIRECTION_IN
        )

        category = categorize_transaction(transaction)
        self.assertEqual(category, 'other')

    def test_aggregate_transactions_by_category(self):
        """Test aggregating transactions by category"""
        # Create various transactions
        StatementDetail.objects.create(
            statement=self.statement,
            item='SALARY',
            transaction_date=date(2025, 1, 15),
            amount=Decimal('2000.00'),
            direction=DIRECTION_IN
        )
        StatementDetail.objects.create(
            statement=self.statement,
            item='GROCERY STORE',
            transaction_date=date(2025, 1, 20),
            amount=Decimal('150.00'),
            direction=DIRECTION_OUT
        )
        StatementDetail.objects.create(
            statement=self.statement,
            item='TRANSFER TO EQ BANK',
            transaction_date=date(2025, 1, 22),
            amount=Decimal('500.00'),
            direction=DIRECTION_OUT
        )
        StatementDetail.objects.create(
            statement=self.statement,
            item='QUESTRADE INVESTMENT',
            transaction_date=date(2025, 1, 25),
            amount=Decimal('300.00'),
            direction=DIRECTION_OUT
        )

        transactions = StatementDetail.objects.filter(statement=self.statement)
        result = aggregate_transactions_by_category(transactions)

        # Check aggregations
        self.assertEqual(result['income'], Decimal('2000.00'))
        self.assertEqual(result['spending'], Decimal('150.00'))
        self.assertEqual(result['transfers'], Decimal('500.00'))
        self.assertEqual(result['investments'], Decimal('300.00'))

        # Check net amount: income - spending - transfers
        expected_net = Decimal('2000.00') - Decimal('150.00') - Decimal('500.00')
        self.assertEqual(result['net_amount'], expected_net)

        # Check transaction lists
        self.assertEqual(len(result['income_transactions']), 1)
        self.assertEqual(len(result['spending_transactions']), 1)
        self.assertEqual(len(result['transfer_transactions']), 1)
        self.assertEqual(len(result['investment_transactions']), 1)

    def test_is_payment_transaction(self):
        """Test identifying payment transactions"""
        self.assertTrue(is_payment_transaction('PAYMENT RECEIVED'))
        self.assertTrue(is_payment_transaction('ROYAL BANK OF CANADA TORONTO'))
        self.assertTrue(is_payment_transaction('payment received'))
        self.assertFalse(is_payment_transaction('GROCERY STORE'))
        self.assertFalse(is_payment_transaction('SALARY'))

    def test_aggregate_empty_transactions(self):
        """Test aggregating empty transaction set"""
        transactions = StatementDetail.objects.none()
        result = aggregate_transactions_by_category(transactions)

        self.assertEqual(result['income'], Decimal('0.00'))
        self.assertEqual(result['spending'], Decimal('0.00'))
        self.assertEqual(result['transfers'], Decimal('0.00'))
        self.assertEqual(result['investments'], Decimal('0.00'))
        self.assertEqual(result['net_amount'], Decimal('0.00'))
        self.assertEqual(len(result['income_transactions']), 0)
