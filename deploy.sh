#!/bin/bash

# Google Cloud deployment script for Money Tracking app

echo "🚀 Starting deployment to Google Cloud..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Set variables
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_NAME="money-tracking"

echo "📋 Project ID: $PROJECT_ID"
echo "🌍 Region: $REGION"
echo "🔧 Service: $SERVICE_NAME"

# Enable required APIs
echo "🔌 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com

# Build and deploy
echo "🏗️ Building and deploying..."
gcloud builds submit --config deployment/cloudbuild.yaml .

echo "✅ Deployment completed!"
echo "🌐 Your app should be available at: https://$SERVICE_NAME-$PROJECT_ID.a.run.app"
