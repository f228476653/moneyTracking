#!/bin/bash

# Script to create the database and run migrations
# This will set up the complete database schema for the application

echo "🗄️  Setting up database for money tracking application..."

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No Google Cloud project set. Please run:"
    echo "   gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Project ID: $PROJECT_ID"

# Check if Cloud SQL instance exists
if ! gcloud sql instances describe money-tracking-db --quiet 2>/dev/null; then
    echo "❌ Cloud SQL instance 'money-tracking-db' not found"
    exit 1
fi

# Check if database exists
echo "🔍 Checking if database 'money_tracking' exists..."
DB_EXISTS=$(gcloud sql databases list --instance=money-tracking-db --filter="name=money_tracking" --format="value(name)" 2>/dev/null)

if [ -z "$DB_EXISTS" ]; then
    echo "📊 Creating database 'money_tracking'..."
    gcloud sql databases create money_tracking --instance=money-tracking-db
    
    if [ $? -eq 0 ]; then
        echo "✅ Database 'money_tracking' created successfully!"
    else
        echo "❌ Failed to create database. Please check the error above."
        exit 1
    fi
else
    echo "✅ Database 'money_tracking' already exists"
fi

# Run migrations using Cloud Run Job
echo "🔧 Running Django migrations..."
gcloud run jobs create migrate-db-$(date +%s) \
    --image gcr.io/$PROJECT_ID/money-tracking:latest \
    --region us-central1 \
    --set-env-vars="DJANGO_SETTINGS_MODULE=bank_parser.settings,DEBUG=False,DB_ENGINE=django.db.backends.postgresql,DB_NAME=money_tracking,DB_USER=postgres,DB_PASSWORD=postgres123,DB_HOST=/cloudsql/$PROJECT_ID:us-central1:money-tracking-db,DB_PORT=5432" \
    --set-cloudsql-instances=$PROJECT_ID:us-central1:money-tracking-db \
    --command="python" \
    --args="manage.py,migrate" \
    --max-retries=3 \
    --parallelism=1 \
    --task-timeout=300

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully!"
    echo "🎉 Database setup is complete!"
    echo "🔄 You can now access your application at the Cloud Run URL"
else
    echo "❌ Migration failed. Please check the error above."
    exit 1
fi
