# Money Tracking - Bank Statement Parser

A Django application for parsing and analyzing bank statements from multiple formats (CSV, Excel, PDF, TXT).

## 🎯 Features

- **Multi-Bank Support**: Parse statements from American Express, TD Bank, RBC, BMO, EQ Bank, Wealthsimple
- **Multiple Formats**: CSV, Excel (.xlsx), PDF, and Text files
- **Automatic Detection**: Bank-specific parsers with automatic format detection
- **Transaction Analysis**: Categorize and analyze spending patterns
- **Visual Reports**: Interactive Plotly charts and financial summaries
- **Investment Tracking**: Track investment accounts and performance
- **Web Interface**: User-friendly Django interface
- **Cloud Deployment**: Production-ready for Google Cloud Run

## 🚀 Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/YOUR-USERNAME/moneyTracking.git
cd moneyTracking

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your SECRET_KEY

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

Visit: http://localhost:8000

### Docker (Local Development)

```bash
# Start with Docker Compose
bash docker-deploy.sh

# Or manually
docker-compose up -d
```

Visit: http://localhost:8000

## 📦 Deployment

### Deploy to Google Cloud Run

```bash
# First time setup
bash deploy-gcp-free.sh

# Regular deployments
bash deploy-production.sh
```

**Full Deployment Guide**: See [DEPLOYMENT_GUIDE_CLOUDRUN.md](DEPLOYMENT_GUIDE_CLOUDRUN.md)

### GitHub Actions Auto-Deploy

Every push to `main` automatically deploys to Cloud Run.

**Setup Guide**: See [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)

## 🏦 Supported Banks

### Credit Cards
- **American Express** - CSV format
- **TD Credit Card** - CSV format

### Bank Accounts
- **TD Bank** - CSV format (chequing accounts)
- **RBC Business** - CSV format
- **EQ Bank Joint** - CSV format
- **BMO Bank** - CSV format

### Investments
- **Wealthsimple RRSP** - PDF format

### Generic Parsers
- **CSV Parser** - Generic CSV files
- **Excel Parser** - Generic .xlsx files
- **Text Parser** - Generic text files

## 📊 Architecture

```
moneyTracking/
├── statements/           # Main app
│   ├── parsers/         # 10+ bank-specific parsers
│   │   ├── factory.py   # Parser factory (strategy pattern)
│   │   ├── base.py      # Base parser class
│   │   ├── amex_parser.py
│   │   ├── td_parser.py
│   │   └── ...
│   ├── models/          # Data models
│   │   ├── account.py
│   │   ├── statement.py
│   │   └── statement_detail.py
│   ├── views/           # View logic
│   ├── forms/           # Form handling
│   ├── tests/           # 65+ unit tests
│   ├── constants.py     # Configuration constants
│   ├── exceptions.py    # Custom exceptions
│   ├── utils.py         # Utility functions
│   └── validators.py    # File validators
├── accounts/            # User authentication
├── templates/           # Django templates
├── deployment/          # Docker configurations
├── .github/workflows/   # GitHub Actions CI/CD
└── manage.py
```

## 🧪 Testing

```bash
# Run all tests
python manage.py test statements.tests

# Run specific test file
python manage.py test statements.tests.test_models

# With coverage
coverage run manage.py test statements.tests
coverage report
```

**Test Coverage**: 65+ tests covering parsers, models, views, and utilities

## 🔧 Key Components

### Parser System (Strategy Pattern)

```python
from statements.factory import StatementParserFactory

# Automatic parser selection
factory = StatementParserFactory()
statement_meta, transactions = factory.parse_statement(file_content, filename)
```

### Supported Models

- **Account**: Bank/credit card/investment accounts
- **Statement**: Individual bank statements
- **StatementDetail**: Transaction details
- **InvestmentData**: Investment holdings
- **AccountValue**: Account value tracking over time

### Transaction Categorization

Automatically categorizes transactions:
- **Income**: Salary, deposits (IN direction)
- **Spending**: Regular expenses (OUT direction)
- **Investments**: Questrade, mutual funds, GICs
- **Transfers**: Between accounts (EQ Bank, pay vendor)

## 📝 Environment Variables

Required environment variables (in `.env`):

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False

# Database (Production - Cloud SQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=money_tracking
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=/cloudsql/PROJECT:REGION:INSTANCE
DB_PORT=5432

# Or SQLite (Development)
DB_ENGINE=django.db.backends.sqlite3
```

See `.env.example` for full template.

## 🔒 Security

- File upload validation (10MB limit)
- Allowed extensions: `.csv`, `.xlsx`, `.xls`, `.pdf`, `.txt`
- CSRF protection
- Secure password hashing (PBKDF2/Argon2)
- Session security (HTTPOnly, Secure cookies)
- SQL injection protection (Django ORM)
- XSS prevention

**Security Guide**: See [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md)

## ⚡ Performance

- **Database Indexes**: 9 indexes on frequently queried fields
- **Query Optimization**: Prefetch and select_related to avoid N+1 queries
- **Result Caching**: 1-hour cache on expensive calculations
- **Async Processing**: Background jobs for migrations

**Performance**: 60-80% faster queries with indexes and caching

## 📚 Documentation

- **[README.md](README.md)** - This file (overview)
- **[DEPLOYMENT_GUIDE_CLOUDRUN.md](DEPLOYMENT_GUIDE_CLOUDRUN.md)** - Complete deployment guide
- **[QUICK_START_DEPLOYMENT.md](QUICK_START_DEPLOYMENT.md)** - Quick deployment reference
- **[GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)** - CI/CD setup
- **[SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md)** - Security best practices
- **[CODE_REVIEW_SUMMARY.md](CODE_REVIEW_SUMMARY.md)** - Code improvements log

## 🛠️ Tech Stack

**Backend:**
- Django 4.2.7+
- Python 3.9+
- PostgreSQL (production) / SQLite (development)

**Data Processing:**
- pandas (CSV/Excel parsing)
- PyPDF2, pdfplumber (PDF parsing)
- python-dateutil (date parsing)

**Frontend:**
- Django templates
- Bootstrap 5
- Plotly (interactive charts)

**Deployment:**
- Google Cloud Run (serverless containers)
- Cloud SQL (PostgreSQL)
- Cloud Build (CI/CD)
- Docker

## 🔄 Development Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and test
python manage.py test

# Commit and push
git add .
git commit -m "Add new feature"
git push origin feature/my-feature

# Create PR on GitHub
# Tests run automatically

# After merge to main
# Automatically deploys to Cloud Run!
```

## 📊 Project Stats

- **Lines of Code**: ~8,000+ lines
- **Parsers**: 10 specialized parsers
- **Tests**: 65+ comprehensive tests
- **Models**: 5 main data models
- **Views**: 9 view functions
- **Templates**: 9 HTML templates

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

**Code Standards:**
- Follow Django best practices
- Write tests for new features
- Update documentation
- Run `flake8` linting

## 📄 License

This project is private. All rights reserved.

## 🐛 Troubleshooting

### Common Issues

**File Upload Fails**
- Check file size (max 10MB)
- Verify file extension (csv, xlsx, xls, pdf, txt)
- Check logs: `tail -f logs/django.log`

**Parser Error**
- Verify file format matches bank type
- Check for corrupted CSV/PDF
- Try generic CSV parser

**Database Connection**
- Verify Cloud SQL is running
- Check connection string in `.env`
- Review Cloud Run logs

**Deployment Fails**
- Check GitHub Actions logs
- Verify all secrets are set
- Run tests locally first

## 📞 Support

For issues or questions:
1. Check documentation in `/docs`
2. Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Check GitHub Issues
4. Review deployment logs

## 🎯 Roadmap

- [ ] Add more bank parsers (Chase, Wells Fargo)
- [ ] Machine learning categorization
- [ ] Budget tracking
- [ ] Mobile app
- [ ] Real-time sync with bank APIs
- [ ] Multi-currency support

---

**Last Updated**: 2025-11-09
**Version**: 2.0
**Status**: Production Ready ✅
