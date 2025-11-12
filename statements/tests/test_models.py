"""
Tests for the statements models
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from decimal import Decimal
from datetime import date

from ..models import Account, Statement, StatementDetail

User = get_user_model()


class AccountModelTest(TestCase):
    """Test cases for Account model"""

    def setUp(self):
        """Set up test fixtures"""
        self.account = Account.objects.create(
            account_abbr='TEST_CHQ',
            bank_name='Test Bank',
            account_number='12345678',
            account_type='BANK'
        )

    def test_account_creation(self):
        """Test that account is created correctly"""
        self.assertEqual(self.account.account_abbr, 'TEST_CHQ')
        self.assertEqual(self.account.bank_name, 'Test Bank')
        self.assertEqual(self.account.account_type, 'BANK')

    def test_account_str(self):
        """Test account string representation"""
        expected = "Test Bank - TEST_CHQ (Bank)"
        self.assertEqual(str(self.account), expected)

    def test_account_unique_abbr(self):
        """Test that account_abbr must be unique"""
        with self.assertRaises(Exception):
            Account.objects.create(
                account_abbr='TEST_CHQ',  # Duplicate
                bank_name='Another Bank',
                account_number='87654321',
                account_type='BANK'
            )

    def test_account_types_choices(self):
        """Test that all account types are valid"""
        valid_types = ['CREDIT_CARD', 'INVESTMENT', 'BANK']
        for account_type in valid_types:
            account = Account.objects.create(
                account_abbr=f'TEST_{account_type}',
                bank_name='Test Bank',
                account_number='12345',
                account_type=account_type
            )
            self.assertEqual(account.account_type, account_type)


class StatementModelTest(TestCase):
    """Test cases for Statement model"""

    def setUp(self):
        """Set up test fixtures"""
        cache.clear()  # Clear cache before each test

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

    def test_statement_creation(self):
        """Test that statement is created correctly"""
        self.assertEqual(self.statement.account, self.account)
        self.assertEqual(self.statement.source_file, 'test_statement.csv')
        self.assertEqual(self.statement.statement_type, 'CSV')

    def test_statement_str(self):
        """Test statement string representation"""
        expected = "Test Bank - TEST_CHQ (2025-01-01 to 2025-01-31)"
        self.assertEqual(str(self.statement), expected)

    def test_total_credits_empty(self):
        """Test total credits with no transactions"""
        self.assertEqual(self.statement.total_credits, Decimal('0.00'))

    def test_total_debits_empty(self):
        """Test total debits with no transactions"""
        self.assertEqual(self.statement.total_debits, Decimal('0.00'))

    def test_net_amount_empty(self):
        """Test net amount with no transactions"""
        self.assertEqual(self.statement.net_amount, Decimal('0.00'))

    def test_total_credits_with_transactions(self):
        """Test total credits with IN transactions"""
        StatementDetail.objects.create(
            statement=self.statement,
            item='Salary',
            transaction_date=date(2025, 1, 15),
            amount=Decimal('1000.00'),
            direction='IN'
        )
        StatementDetail.objects.create(
            statement=self.statement,
            item='Bonus',
            transaction_date=date(2025, 1, 20),
            amount=Decimal('500.00'),
            direction='IN'
        )

        # Clear cache to force recalculation
        cache.clear()

        self.assertEqual(self.statement.total_credits, Decimal('1500.00'))

    def test_total_debits_with_transactions(self):
        """Test total debits with OUT transactions"""
        StatementDetail.objects.create(
            statement=self.statement,
            item='Rent',
            transaction_date=date(2025, 1, 1),
            amount=Decimal('1200.00'),
            direction='OUT'
        )
        StatementDetail.objects.create(
            statement=self.statement,
            item='Utilities',
            transaction_date=date(2025, 1, 5),
            amount=Decimal('150.00'),
            direction='OUT'
        )

        # Clear cache to force recalculation
        cache.clear()

        self.assertEqual(self.statement.total_debits, Decimal('1350.00'))

    def test_net_amount_with_transactions(self):
        """Test net amount calculation"""
        StatementDetail.objects.create(
            statement=self.statement,
            item='Income',
            transaction_date=date(2025, 1, 15),
            amount=Decimal('2000.00'),
            direction='IN'
        )
        StatementDetail.objects.create(
            statement=self.statement,
            item='Expense',
            transaction_date=date(2025, 1, 5),
            amount=Decimal('500.00'),
            direction='OUT'
        )

        # Clear cache to force recalculation
        cache.clear()

        self.assertEqual(self.statement.net_amount, Decimal('1500.00'))

    def test_cache_invalidation_on_detail_save(self):
        """Test that cache is invalidated when detail is saved"""
        # Create initial transaction
        detail = StatementDetail.objects.create(
            statement=self.statement,
            item='Income',
            transaction_date=date(2025, 1, 15),
            amount=Decimal('1000.00'),
            direction='IN'
        )

        # Access property to cache it
        cache.clear()
        first_total = self.statement.total_credits
        self.assertEqual(first_total, Decimal('1000.00'))

        # Modify the transaction
        detail.amount = Decimal('1500.00')
        detail.save()

        # Cache should be cleared, so we get updated value
        second_total = self.statement.total_credits
        self.assertEqual(second_total, Decimal('1500.00'))

    def test_clear_cache_method(self):
        """Test manual cache clearing"""
        # Create transaction and cache it
        StatementDetail.objects.create(
            statement=self.statement,
            item='Income',
            transaction_date=date(2025, 1, 15),
            amount=Decimal('1000.00'),
            direction='IN'
        )

        cache.clear()
        _ = self.statement.total_credits  # Cache it

        # Manually clear cache
        self.statement.clear_cache()

        # Verify cache is cleared by checking it doesn't exist
        cache_key = self.statement._get_cache_key('total_credits')
        self.assertIsNone(cache.get(cache_key))


class StatementDetailModelTest(TestCase):
    """Test cases for StatementDetail model"""

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

    def test_statement_detail_creation(self):
        """Test that statement detail is created correctly"""
        detail = StatementDetail.objects.create(
            statement=self.statement,
            item='Grocery Store',
            transaction_date=date(2025, 1, 15),
            amount=Decimal('150.50'),
            direction='OUT'
        )

        self.assertEqual(detail.statement, self.statement)
        self.assertEqual(detail.item, 'Grocery Store')
        self.assertEqual(detail.amount, Decimal('150.50'))
        self.assertEqual(detail.direction, 'OUT')

    def test_statement_detail_str(self):
        """Test statement detail string representation"""
        detail = StatementDetail.objects.create(
            statement=self.statement,
            item='Salary',
            transaction_date=date(2025, 1, 15),
            amount=Decimal('5000.00'),
            direction='IN'
        )

        expected = "Salary - 5000.00 (IN) on 2025-01-15"
        self.assertEqual(str(detail), expected)

    def test_direction_choices(self):
        """Test that direction must be IN or OUT"""
        valid_directions = ['IN', 'OUT']
        for direction in valid_directions:
            detail = StatementDetail.objects.create(
                statement=self.statement,
                item=f'Test {direction}',
                transaction_date=date(2025, 1, 15),
                amount=Decimal('100.00'),
                direction=direction
            )
            self.assertEqual(detail.direction, direction)

    def test_amount_validation(self):
        """Test that amount must be positive"""
        with self.assertRaises(Exception):
            StatementDetail.objects.create(
                statement=self.statement,
                item='Invalid Transaction',
                transaction_date=date(2025, 1, 15),
                amount=Decimal('-100.00'),  # Negative amount
                direction='OUT'
            )

    def test_ordering(self):
        """Test that details are ordered by transaction_date descending"""
        detail1 = StatementDetail.objects.create(
            statement=self.statement,
            item='First',
            transaction_date=date(2025, 1, 10),
            amount=Decimal('100.00'),
            direction='OUT'
        )
        detail2 = StatementDetail.objects.create(
            statement=self.statement,
            item='Second',
            transaction_date=date(2025, 1, 20),
            amount=Decimal('200.00'),
            direction='OUT'
        )
        detail3 = StatementDetail.objects.create(
            statement=self.statement,
            item='Third',
            transaction_date=date(2025, 1, 15),
            amount=Decimal('150.00'),
            direction='OUT'
        )

        # Get all details (should be ordered by date descending)
        details = StatementDetail.objects.filter(statement=self.statement)

        self.assertEqual(details[0], detail2)  # Jan 20
        self.assertEqual(details[1], detail3)  # Jan 15
        self.assertEqual(details[2], detail1)  # Jan 10
