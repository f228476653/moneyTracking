#!/bin/bash

# Ultra-cost-optimized Google Cloud deployment script
# Designed to stay within free tier limits

echo "🚀 Starting FREE Google Cloud deployment..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    echo "   Download from: https://cloud.google.com/sdk/docs/install"
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

# Enable required APIs
echo "🔌 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com

# Check if Cloud SQL instance exists
echo "🗄️  Checking Cloud SQL instance..."
if ! gcloud sql instances describe money-tracking-db --quiet 2>/dev/null; then
    echo "📦 Creating Cloud SQL instance (FREE TIER)..."
    gcloud sql instances create money-tracking-db \
        --database-version=POSTGRES_13 \
        --tier=db-f1-micro \
        --region=us-central1 \
        --root-password=postgres123
    echo "✅ Cloud SQL instance created (FREE TIER ELIGIBLE)"
    
    echo "⏳ Waiting for instance to be ready..."
    while true; do
        STATE=$(gcloud sql instances describe money-tracking-db --format='value(state)' 2>/dev/null)
        if [ "$STATE" = "RUNNABLE" ]; then
            echo "✅ Instance is ready!"
            break
        elif [ "$STATE" = "PENDING_CREATE" ]; then
            echo "⏳ Still creating... waiting 30 seconds"
            sleep 30
        else
            echo "❌ Instance state: $STATE"
            sleep 10
        fi
    done
    
    echo "📊 Creating database..."
    gcloud sql databases create money_tracking --instance=money-tracking-db
    
    echo "👤 Creating database user..."
    gcloud sql users create postgres \
        --instance=money-tracking-db \
        --password=postgres123
else
    echo "✅ Cloud SQL instance already exists"
    # Check if instance is ready
    INSTANCE_STATE=$(gcloud sql instances describe money-tracking-db --format='value(state)')
    if [ "$INSTANCE_STATE" != "RUNNABLE" ]; then
        echo "⏳ Waiting for instance to be ready..."
        while true; do
            STATE=$(gcloud sql instances describe money-tracking-db --format='value(state)' 2>/dev/null)
            if [ "$STATE" = "RUNNABLE" ]; then
                echo "✅ Instance is ready!"
                break
            elif [ "$STATE" = "PENDING_CREATE" ]; then
                echo "⏳ Still creating... waiting 30 seconds"
                sleep 30
            else
                echo "❌ Instance state: $STATE"
                sleep 10
            fi
        done
    fi
fi

# Build and deploy
echo "🏗️  Building and deploying..."
gcloud builds submit --config cloudbuild-simple.yaml .

# Run migrations
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

# Get service URL
SERVICE_URL=$(gcloud run services describe money-tracking --region=us-central1 --format='value(status.url)' 2>/dev/null)

echo "✅ Deployment completed!"
echo "🌐 Your app is available at: $SERVICE_URL"
