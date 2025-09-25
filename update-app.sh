#!/bin/bash

# Simple script to update your deployed app

echo "🔄 Updating Money Tracking App..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No Google Cloud project set. Please run:"
    echo "   gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Project ID: $PROJECT_ID"

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not logged in to Google Cloud. Please run:"
    echo "   gcloud auth login"
    exit 1
fi

# Build and deploy new version
echo "🏗️  Building and deploying new version..."
gcloud builds submit --config cloudbuild-simple.yaml .

# Check if migration is needed
echo "🔍 Checking if database migration is needed..."
echo "Do you want to run database migrations? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "🔧 Running database migrations..."
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
    
    echo "⏳ Waiting for migration to complete..."
    sleep 10
fi

# Get service URL
SERVICE_URL=$(gcloud run services describe money-tracking --region=us-central1 --format='value(status.url)' 2>/dev/null)

echo "✅ Update completed!"
echo "🌐 Your updated app is available at: $SERVICE_URL"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: gcloud logging read 'resource.type=cloud_run_revision' --limit=50"
echo "   View service: gcloud run services describe money-tracking --region=us-central1"
echo "   Rollback: gcloud run services update-traffic money-tracking --to-revisions=REVISION_NAME=100 --region=us-central1"
