# Deploy Docker Compose App to Google Cloud

Simple guide to deploy your Django + PostgreSQL app to Google Cloud Run with Cloud SQL.

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google Cloud SDK** installed
3. **Docker** installed (for local testing)

## Quick Start

### 1. Setup Google Cloud
```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable billing (required for Cloud SQL)
```

### 2. Deploy Everything
```bash
# Just run this one command:
./deploy-gcp.sh
```

That's it! Your app will be deployed to Google Cloud Run.

## What Gets Created

### Cloud Run Service
- **Name**: money-tracking
- **Region**: us-central1
- **Port**: 8080
- **Auto-scaling**: 0-10 instances

### Cloud SQL Database
- **Instance**: money-tracking-db
- **Database**: money_tracking
- **User**: postgres
- **Password**: postgres123
- **Tier**: db-f1-micro (cheapest)

### Container Registry
- **Image**: gcr.io/YOUR_PROJECT_ID/money-tracking
- **Auto-built** from your Dockerfile.prod

## Manual Steps (if needed)

### 1. Create Cloud SQL Instance
```bash
gcloud sql instances create money-tracking-db \
    --database-version=POSTGRES_13 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=changeme123

gcloud sql databases create money_tracking --instance=money-tracking-db
gcloud sql users create postgres --instance=money-tracking-db --password=postgres123
```

### 2. Build and Deploy
```bash
gcloud builds submit --config cloudbuild-simple.yaml .
```

### 3. Run Migrations
```bash
gcloud run jobs create migrate-db \
    --image gcr.io/YOUR_PROJECT_ID/money-tracking:latest \
    --region us-central1 \
    --set-env-vars="DJANGO_SETTINGS_MODULE=bank_parser.settings,DEBUG=False,DB_ENGINE=django.db.backends.postgresql,DB_NAME=money_tracking,DB_USER=postgres,DB_PASSWORD=postgres123,DB_HOST=/cloudsql/YOUR_PROJECT_ID:us-central1:money-tracking-db,DB_PORT=5432" \
    --add-cloudsql-instances=YOUR_PROJECT_ID:us-central1:money-tracking-db \
    --command="python" \
    --args="manage.py,migrate"

gcloud run jobs execute migrate-db --region us-central1 --wait
```

## File Structure

```
moneyTracking/
├── docker-compose.yml        # Local development
├── Dockerfile               # Local development
├── Dockerfile.prod          # Production (Google Cloud)
├── cloudbuild-simple.yaml   # Google Cloud Build config
├── deploy-gcp.sh           # One-command deployment
└── GCP_DEPLOYMENT.md       # This guide
```

## Local vs Production

### Local Development
```bash
# Uses docker-compose.yml + Dockerfile
./docker-deploy.sh
# → http://localhost:8000
```

### Production (Google Cloud)
```bash
# Uses cloudbuild-simple.yaml + Dockerfile.prod
./deploy-gcp.sh
# → https://money-tracking-xxx.run.app
```

## Key Differences

| Aspect | Local | Production |
|--------|-------|------------|
| Database | PostgreSQL in Docker | Cloud SQL |
| Static Files | WhiteNoise | Collected at build |
| Debug | True | False |
| Port | 8000 | 8080 |
| Scaling | Single instance | Auto-scaling |

## Cost Optimization

### Development
- **Cloud SQL**: db-f1-micro (free tier eligible)
- **Cloud Run**: Pay per request (very cheap)
- **Container Registry**: Small storage cost

### Estimated Monthly Cost
- **Cloud SQL**: $0-7 (free tier: 1 instance, 1GB)
- **Cloud Run**: $0-5 (depends on traffic)
- **Total**: ~$0-12/month for low traffic

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Database Connection Failed**
   ```bash
   # Check if Cloud SQL is running
   gcloud sql instances describe money-tracking-db
   
   # Check if database exists
   gcloud sql databases list --instance=money-tracking-db
   ```

3. **Build Failed**
   ```bash
   # Check build logs
   gcloud builds log --stream
   ```

4. **App Not Starting**
   ```bash
   # Check Cloud Run logs
   gcloud logging read "resource.type=cloud_run_revision" --limit=50
   ```

### Debug Commands

```bash
# View all services
gcloud run services list

# View service details
gcloud run services describe money-tracking --region=us-central1

# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# Connect to database
gcloud sql connect money-tracking-db --user=postgres
```

## Security Notes

- Change default passwords in production
- Use Google Secret Manager for sensitive data
- Enable Cloud SQL SSL
- Set up proper IAM roles
- Monitor access logs

## Scaling

### Automatic Scaling
- Cloud Run scales to 0 when no traffic
- Scales up to 10 instances automatically
- Each instance can handle ~1000 requests/second

### Manual Scaling
```bash
# Set minimum instances
gcloud run services update money-tracking \
    --region=us-central1 \
    --min-instances=1
```

## Updates

### Update Your App
```bash
# Just push your changes and run:
./deploy-gcp.sh
```

### Update Database
```bash
# Create a new migration job
gcloud run jobs create migrate-db-$(date +%s) \
    --image gcr.io/YOUR_PROJECT_ID/money-tracking:latest \
    --region us-central1 \
    --set-env-vars="..." \
    --add-cloudsql-instances=YOUR_PROJECT_ID:us-central1:money-tracking-db \
    --command="python" \
    --args="manage.py,migrate"
```

## Cleanup

### Delete Everything
```bash
# Delete Cloud Run service
gcloud run services delete money-tracking --region=us-central1

# Delete Cloud SQL instance
gcloud sql instances delete money-tracking-db

# Delete container images
gcloud container images delete gcr.io/YOUR_PROJECT_ID/money-tracking:latest
```

This setup gives you the simplicity of Docker Compose locally with the power of Google Cloud for production! 🚀
