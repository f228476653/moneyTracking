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
| `GCP_SA_KEY` | The entire JSON content of the service account key | `{"type": "service_account", "project_id": "..."}` |
| `DJANGO_SECRET_KEY` | Django secret key for production | `your-django-secret-key` |
| `DATABASE_URL` | Supabase PostgreSQL connection URL | `postgresql://user:pass@db.project.supabase.co:5432/postgres` |

## Step 4: Set Up Supabase Database

1. Go to [Supabase](https://supabase.com/) and create an account
2. Create a new project
3. Go to **Settings** > **Database**
4. Copy the **Connection string** (it looks like `postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres`)
5. Use this as your `DATABASE_URL` secret in GitHub

Note: The database will be automatically created by Supabase. No manual setup required!

## Step 5: Enable Required APIs

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable secretmanager.googleapis.com
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
2. **Database Connection Failed**: Verify your DATABASE_URL secret is correct and Supabase database is accessible
3. **Build Failed**: Check that all dependencies are in `requirements.txt`
4. **Migration Failed**: Ensure DATABASE_URL is properly configured in GitHub Secrets

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

- Supabase offers a generous free tier for development
- Consider upgrading to a paid plan for production workloads
- Monitor Cloud Run usage in Google Cloud Console
- Set up billing alerts for Cloud Run and Cloud Build

## Next Steps

After successful deployment:

1. Set up a custom domain (optional)
2. Configure SSL certificates
3. Set up monitoring and logging
4. Configure backup strategies
5. Set up staging environment
