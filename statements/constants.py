"""
Constants for the statements app
"""

# Transaction categorization keywords
TRANSFER_KEYWORDS = ['EQ BANK', 'PAY EMP-VENDOR']
INVESTMENT_KEYWORDS = ['INVESTMENTS', 'QUESTRADE', 'MUTUAL FUNDS', 'GIC']
PAYMENT_KEYWORDS = ['ROYAL BANK OF CANADA TORONTO', 'PAYMENT RECEIVED']

# Account types
ACCOUNT_TYPE_BANK = 'BANK'
ACCOUNT_TYPE_CREDIT_CARD = 'CREDIT_CARD'
ACCOUNT_TYPE_INVESTMENT = 'INVESTMENT'

# Transaction directions
DIRECTION_IN = 'IN'
DIRECTION_OUT = 'OUT'

# Statement types
STATEMENT_TYPE_CSV = 'CSV'
STATEMENT_TYPE_EXCEL = 'EXCEL'
STATEMENT_TYPE_PDF = 'PDF'
STATEMENT_TYPE_TXT = 'TXT'
STATEMENT_TYPE_OTHER = 'OTHER'

# Date formats
COMMON_DATE_FORMATS = [
    '%Y-%m-%d',
    '%m/%d/%Y',
    '%d/%m/%Y',
    '%Y/%m/%d',
    '%m-%d-%Y',
    '%d-%m-%Y',
    '%b %d, %Y',
    '%B %d, %Y',
    '%d %b %Y',
    '%d %B %Y'
]

# File upload limits
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.xls', '.pdf', '.txt']
