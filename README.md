# Bank Statement Parser

A Django application for parsing and analyzing bank statements from CSV files.

## Features

- **CSV Support**: Parse statements from CSV files
- **Automatic Detection**: Bank name, transaction dates, amounts, and descriptions
- **Transaction Analysis**: Categorize and analyze spending patterns
- **Visual Reports**: Interactive charts and financial summaries
- **Web Interface**: User-friendly upload and management interface

## CSV Parsing Capabilities

### How CSV Parsing Works

The CSV parser automatically detects and extracts transaction data from bank statement CSV files:

1. **Column Detection**: Automatically identifies date, amount, and description columns
2. **Data Parsing**: Parses transaction details with proper formatting
3. **Bank Detection**: Identifies bank from filename and content
4. **Metadata Extraction**: Account numbers, statement periods, account types

### Supported CSV Formats

- **Standard CSV**: Comma-separated values with headers
- **Bank-specific formats**: Automatically adapts to different bank layouts
- **Multiple encodings**: UTF-8, Latin-1, CP1252 support

### CSV Parsing Process

```python
# Example usage
from statements.parsers import StatementParserFactory

factory = StatementParserFactory()

# Parse CSV file
with open('bank_statement.csv', 'rb') as f:
    file_content = f.read()

statement_meta, transactions = factory.parse_statement(file_content, 'bank_statement.csv')

# Results
print(f"Bank: {statement_meta['bank_name']}")
print(f"Account: {statement_meta['account_number']}")
print(f"Period: {statement_meta['statement_from_date']} to {statement_meta['statement_to_date']}")
print(f"Transactions: {len(transactions)}")
```

### Installation Requirements

Add these dependencies to your `requirements.txt`:

```txt
Django>=4.2.7
pandas>=2.2.0
python-dateutil>=2.8.2
```

Install with:
```bash
pip install -r requirements.txt
```

### CSV Parsing Features

- **Automatic Bank Detection**: Identifies bank from filename and content
- **Metadata Extraction**: Account numbers, statement periods, account types
- **Transaction Parsing**: Date, amount, description, and direction
- **Multiple Date Formats**: Supports various date formats
- **Amount Parsing**: Handles currency symbols, commas, and parentheses
- **Error Handling**: Graceful handling of malformed data
- **Bank-Specific Logic**: Customized parsing for different banks

### Usage Examples

#### Basic CSV Upload
```python
# In Django view
def upload_csv(request):
    if request.method == 'POST':
        uploaded_file = request.FILES['csv_file']
        file_content = uploaded_file.read()
        
        parser_factory = StatementParserFactory()
        statement_meta, transactions = parser_factory.parse_statement(
            file_content, uploaded_file.name
        )
        
        # Save to database
        statement = Statement.objects.create(
            bank_name=statement_meta['bank_name'],
            account_number=statement_meta['account_number'],
            statement_from_date=statement_meta['statement_from_date'],
            statement_to_date=statement_meta['statement_to_date'],
            statement_type='CSV'
        )
```

#### Supported Banks
```python
# Automatically detects:
# - Chase Bank (from filename containing 'chase')
# - Wells Fargo (from filename containing 'wells' or 'fargo')
# - Bank of America (from filename containing 'bank' and 'america')
# - Citibank (from filename containing 'citi')
# - TD Bank (from filename containing 'td')
```

### Testing CSV Parsing

Run the test script to verify CSV parsing functionality:

```bash
python test_csv_parser.py
```

### Troubleshooting

#### Common Issues

1. **No transactions extracted**
   - Check if CSV has proper headers
   - Verify date and amount formats match expected patterns
   - Ensure CSV is properly formatted

2. **Encoding issues**
   - Try different file encodings (UTF-8, Latin-1, CP1252)
   - Check for special characters in the CSV

3. **Column detection problems**
   - Verify column headers contain expected keywords
   - Check for extra spaces or special characters in headers

4. **Bank detection issues**
   - Include bank name in filename for better detection
   - Check filename format matches expected patterns

### Performance Considerations

- **Fast processing**: CSV parsing is very efficient
- **Memory efficient**: Processes files line by line
- **Large files**: Handles large CSV files without issues

### Security Notes

- Validate CSV files before processing
- Implement file size limits
- Sanitize extracted text data
- Use secure file upload handling

## Installation and Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Start the server: `python manage.py runserver`

## Usage

1. Navigate to the upload page
2. Select your bank statement CSV file
3. The system will automatically parse and categorize transactions
4. View detailed reports and analytics

## Contributing

Contributions are welcome! Please ensure your code follows the existing patterns and includes appropriate tests.
# moneyTracking
