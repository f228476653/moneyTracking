"""
Tests for the statements views
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from datetime import date

from ..models import Account, Statement, StatementDetail

User = get_user_model()


class UploadViewTest(TestCase):
    """Test cases for upload_statement view"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.account = Account.objects.create(
            account_abbr='TEST_CHQ',
            bank_name='Test Bank',
            account_number='12345678',
            account_type='BANK'
        )

    def test_upload_view_requires_login(self):
        """Test that upload view requires authentication"""
        response = self.client.get(reverse('upload_statement'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_upload_view_get(self):
        """Test GET request to upload view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('upload_statement'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'statements/upload.html')
        self.assertIn('form', response.context)

    def test_upload_view_invalid_file_extension(self):
        """Test uploading file with invalid extension"""
        self.client.login(username='testuser', password='testpass123')

        # Create a fake file with invalid extension
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile

        invalid_file = SimpleUploadedFile(
            'test.xyz',
            b'Invalid content',
            content_type='application/octet-stream'
        )

        response = self.client.post(reverse('upload_statement'), {
            'account': self.account.id,
            'source_file': invalid_file,
        })

        # Should show error message
        messages = list(response.context['messages'])
        self.assertTrue(any('Unsupported file extension' in str(m) for m in messages))


class IndexViewTest(TestCase):
    """Test cases for index view"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_index_view_requires_login(self):
        """Test that index view requires authentication"""
        response = self.client.get(reverse('statements:index'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_index_view_get(self):
        """Test GET request to index view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('statements:index'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'statements/index.html')
        self.assertIn('recent_statements', response.context)


class ReportsViewTest(TestCase):
    """Test cases for reports view"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

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

    def test_reports_view_requires_login(self):
        """Test that reports view requires authentication"""
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_reports_view_get(self):
        """Test GET request to reports view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('reports'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'statements/reports.html')

    def test_reports_view_with_date_filter(self):
        """Test reports view with date range filter"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(reverse('reports'), {
            'start_date': '2025-01-01',
            'end_date': '2025-01-31'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['start_date'], '2025-01-01')
        self.assertEqual(response.context['end_date'], '2025-01-31')

    def test_reports_view_aggregations(self):
        """Test that reports view calculates aggregations correctly"""
        # Create some transactions
        StatementDetail.objects.create(
            statement=self.statement,
            item='Salary',
            transaction_date=date(2025, 1, 15),
            amount=Decimal('2000.00'),
            direction='IN'
        )
        StatementDetail.objects.create(
            statement=self.statement,
            item='Grocery',
            transaction_date=date(2025, 1, 20),
            amount=Decimal('150.00'),
            direction='OUT'
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('reports'), {
            'start_date': '2025-01-01',
            'end_date': '2025-01-31'
        })

        self.assertEqual(response.status_code, 200)
        # Verify context has expected keys
        self.assertIn('bank_accounts', response.context)
        self.assertIn('credit_accounts', response.context)
