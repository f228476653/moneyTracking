# GitHub Actions CI/CD Setup Guide

This guide will help you set up automated deployment to Google Cloud using GitHub Actions.

## Prerequisites

1. Google Cloud Project with billing enabled
2. GitHub repository with admin access
3. Google Cloud SDK installed locally

## Step 1: Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **IAM & Admin** > **Service Accounts**
3. Click **Create Service Account**
4. Fill in the details:
   - **Name**: `github-actions-deploy`
   - **Description**: `Service account for GitHub Actions deployment`
5. Click **Create and Continue**
6. Add the following roles:
   - **Cloud Run Admin**
   - **Cloud Build Editor**
   - **Cloud SQL Client**
   - **Storage Admin**
   - **Service Account User**
7. Click **Done**

## Step 2: Create Service Account Key

1. Click on the service account you just created
2. Go to the **Keys** tab
3. Click **Add Key** > **Create new key**
4. Choose **JSON** format
5. Download the key file (keep it secure!)

## Step 3: Set Up GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret** and add these secrets:

### Required Secrets:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `GCP_PROJECT_ID` | Your Google Cloud Project ID | `my-project-123456` |
| `GCP_SA_KEY` | The entire JSON content of the service account key | `{"type": "service_account", "project_id": "..."}` |
| `DB_PASSWORD` | Your Cloud SQL database password | `your-secure-password` |

## Step 4: Set Up Cloud SQL Database

If you haven't already, create your Cloud SQL instance:

```bash
# Create Cloud SQL instance
gcloud sql instances create money-tracking-db \
    --database-version=POSTGRES_13 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=YOUR_SECURE_ROOT_PASSWORD

# Create database
gcloud sql databases create money_tracking --instance=money-tracking-db

# Create user
gcloud sql users create postgres \
    --instance=money-tracking-db \
    --password=YOUR_SECURE_PASSWORD
```

## Step 5: Enable Required APIs

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable container.googleapis.com
```

## Step 6: Test the Pipeline

1. Push your code to the `main` branch
2. Go to **Actions** tab in your GitHub repository
3. Watch the workflow run
4. Check the deployment logs for any issues

## Workflow Files

- `.github/workflows/cloudbuild.yml` - Main deployment workflow using Cloud Build
- `.github/workflows/deploy.yml` - Alternative workflow using Docker directly

## Troubleshooting

### Common Issues:

1. **Permission Denied**: Check that the service account has all required roles
2. **Database Connection Failed**: Verify Cloud SQL instance is running and accessible
3. **Build Failed**: Check that all dependencies are in `requirements.txt`
4. **Migration Failed**: Ensure database user has proper permissions

### Debug Steps:

1. Check the GitHub Actions logs
2. Verify all secrets are set correctly
3. Test the Cloud Build locally:
   ```bash
   gcloud builds submit --config deployment/cloudbuild.yaml .
   ```

## Security Notes

- Never commit service account keys to your repository
- Use GitHub Secrets for all sensitive information
- Regularly rotate your service account keys
- Monitor the service account usage in Google Cloud Console

## Cost Optimization

- The `db-f1-micro` instance is suitable for development
- Consider upgrading for production workloads
- Monitor usage in Google Cloud Console
- Set up billing alerts

## Next Steps

After successful deployment:

1. Set up a custom domain (optional)
2. Configure SSL certificates
3. Set up monitoring and logging
4. Configure backup strategies
5. Set up staging environment
