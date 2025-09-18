# Money Tracking App - Google Cloud Deployment Guide

## Overview
This guide will help you deploy the Money Tracking Django application to Google Cloud Platform with secure authentication and password storage.

## Features Added
- ✅ User authentication (login/signup/logout)
- ✅ Secure password hashing with PBKDF2
- ✅ Session security and CSRF protection
- ✅ Google Cloud deployment configuration
- ✅ Docker containerization
- ✅ PostgreSQL database support

## Prerequisites
1. Google Cloud SDK installed
2. Docker installed (for local testing)
3. Python 3.9+ installed locally

## Local Development Setup

### 1. Environment Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd moneyTracking

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp env.example .env

# Edit .env with your settings
nano .env
```

### 2. Database Setup
```bash
# Run migrations
python3 manage.py migrate

# Create superuser
python3 manage.py createsuperuser

# Run development server
python3 manage.py runserver
```

## Google Cloud Deployment

### 1. Initial Setup
```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
```

### 2. Database Setup (Cloud SQL)
```bash
# Create Cloud SQL instance
gcloud sql instances create money-tracking-db \
    --database-version=POSTGRES_13 \
    --tier=db-f1-micro \
    --region=us-central1

# Create database
gcloud sql databases create money_tracking --instance=money-tracking-db

# Create user
gcloud sql users create postgres \
    --instance=money-tracking-db \
    --password=YOUR_SECURE_PASSWORD
```

### 3. Update Configuration
Update `app.yaml` with your database connection details:
```yaml
env_variables:
  DB_HOST: "/cloudsql/YOUR_PROJECT_ID:us-central1:money-tracking-db"
  DB_PASSWORD: "YOUR_SECURE_PASSWORD"
```

### 4. Deploy to Google Cloud
```bash
# Make deployment script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

## Security Features

### Password Security
- Passwords are hashed using PBKDF2 with SHA256
- Minimum password length enforced
- Common password validation
- Password similarity validation

### Session Security
- Secure session cookies (HTTPS only in production)
- HttpOnly cookies prevent XSS
- Session timeout after 1 hour
- Sessions expire on browser close

### CSRF Protection
- CSRF tokens on all forms
- Secure CSRF cookies (HTTPS only in production)
- HttpOnly CSRF cookies

### Additional Security
- XSS protection headers
- Content type sniffing protection
- Clickjacking protection
- Secure file upload handling

## Environment Variables

### Required for Production
```bash
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,*.run.app
DB_ENGINE=django.db.backends.postgresql
DB_NAME=money_tracking
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=/cloudsql/your-project:region:instance-name
DB_PORT=5432
```

## File Structure
```
moneyTracking/
├── accounts/                 # Authentication app
│   ├── models.py            # User profile model
│   ├── views.py             # Login/logout views
│   ├── forms.py             # Authentication forms
│   └── urls.py              # Auth URL patterns
├── statements/              # Main app
├── templates/
│   ├── accounts/            # Auth templates
│   └── statements/          # App templates
├── deployment/              # Deployment configs
│   ├── Dockerfile          # Container config
│   └── cloudbuild.yaml     # Build config
├── app.yaml                # App Engine config
├── deploy.sh               # Deployment script
└── requirements.txt        # Dependencies
```

## Monitoring and Maintenance

### View Logs
```bash
# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# View specific service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=money-tracking"
```

### Database Management
```bash
# Connect to Cloud SQL
gcloud sql connect money-tracking-db --user=postgres

# Create database backup
gcloud sql backups create --instance=money-tracking-db
```

## Troubleshooting

### Common Issues
1. **Migration errors**: Ensure all migrations are applied
2. **Database connection**: Check Cloud SQL instance is running
3. **Static files**: Run `python manage.py collectstatic`
4. **Permissions**: Ensure service account has necessary permissions

### Debug Mode
To enable debug mode temporarily:
```bash
# Update app.yaml
env_variables:
  DEBUG: "True"
```

## Cost Optimization
- Use `db-f1-micro` for development
- Set up automatic scaling limits
- Monitor usage in Google Cloud Console
- Consider using Cloud SQL Proxy for local development

## Security Best Practices
1. Use strong, unique passwords
2. Enable 2FA for Google Cloud accounts
3. Regularly rotate database passwords
4. Monitor access logs
5. Keep dependencies updated
6. Use HTTPS only in production

## Support
For issues or questions:
1. Check the logs first
2. Verify environment variables
3. Test locally before deploying
4. Review Google Cloud documentation
