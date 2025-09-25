# How to Update Your Deployed App

Complete guide for updating your Money Tracking app on Google Cloud.

## 🚀 Quick Update (Recommended)

### **One-Command Update:**
```bash
./update-app.sh
```

This will:
1. ✅ Build new container with your changes
2. ✅ Deploy to Cloud Run
3. ✅ Ask if you want to run migrations
4. ✅ Show you the updated URL

## 📝 Step-by-Step Update Process

### **Step 1: Make Your Changes**
```bash
# Edit your code locally
# For example, update a view:
nano statements/views.py

# Or update templates:
nano templates/statements/index.html
```

### **Step 2: Test Locally (Optional)**
```bash
# Test with Docker Compose first
./docker-deploy.sh

# Visit http://localhost:8000 to test
# Stop when done: docker-compose down
```

### **Step 3: Deploy to Production**
```bash
# Deploy your changes
./update-app.sh
```

## 🔄 Different Update Scenarios

### **1. Code Changes Only**
```bash
# Just run the update script
./update-app.sh
# Answer 'n' when asked about migrations
```

### **2. Database Changes (New Models/Migrations)**
```bash
# First, create migration locally
python manage.py makemigrations

# Then deploy
./update-app.sh
# Answer 'y' when asked about migrations
```

### **3. New Dependencies**
```bash
# Update requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# Deploy
./update-app.sh
```

### **4. Environment Variables**
```bash
# Update cloudbuild-simple.yaml or deploy script
# Then redeploy
./update-app.sh
```

## 🛠️ Manual Update Commands

### **Build and Deploy Only:**
```bash
gcloud builds submit --config cloudbuild-simple.yaml .
```

### **Run Migrations Only:**
```bash
gcloud run jobs create migrate-db-$(date +%s) \
    --image gcr.io/YOUR_PROJECT_ID/money-tracking:latest \
    --region us-central1 \
    --set-env-vars="..." \
    --add-cloudsql-instances=YOUR_PROJECT_ID:us-central1:money-tracking-db \
    --command="python" \
    --args="manage.py,migrate"
```

### **Update Specific Service:**
```bash
gcloud run services update money-tracking \
    --region=us-central1 \
    --image=gcr.io/YOUR_PROJECT_ID/money-tracking:latest
```

## 🔍 Monitoring Your Updates

### **Check Deployment Status:**
```bash
# View service details
gcloud run services describe money-tracking --region=us-central1

# View recent deployments
gcloud run revisions list --service=money-tracking --region=us-central1
```

### **View Logs:**
```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# View specific service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=money-tracking" --limit=50
```

### **Check App Health:**
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe money-tracking --region=us-central1 --format='value(status.url)')
echo "App URL: $SERVICE_URL"

# Test the app
curl $SERVICE_URL
```

## 🔄 Rollback (If Something Goes Wrong)

### **Rollback to Previous Version:**
```bash
# List all revisions
gcloud run revisions list --service=money-tracking --region=us-central1

# Rollback to specific revision
gcloud run services update-traffic money-tracking \
    --to-revisions=REVISION_NAME=100 \
    --region=us-central1
```

### **Emergency Rollback:**
```bash
# Rollback to previous working version
gcloud run services update-traffic money-tracking \
    --to-revisions=LATEST=0,PREVIOUS_REVISION=100 \
    --region=us-central1
```

## 🚨 Troubleshooting Updates

### **Common Issues:**

1. **Build Failed**
   ```bash
   # Check build logs
   gcloud builds log --stream
   
   # Common fixes:
   # - Check Dockerfile.prod syntax
   # - Verify requirements.txt
   # - Check file permissions
   ```

2. **App Not Starting**
   ```bash
   # Check Cloud Run logs
   gcloud logging read "resource.type=cloud_run_revision" --limit=50
   
   # Common fixes:
   # - Check environment variables
   # - Verify database connection
   # - Check port configuration
   ```

3. **Database Migration Failed**
   ```bash
   # Check migration logs
   gcloud logging read "resource.type=cloud_run_job" --limit=50
   
   # Common fixes:
   # - Check database permissions
   # - Verify migration files
   # - Check database connectivity
   ```

## 📊 Update Best Practices

### **Before Updating:**
1. ✅ Test changes locally
2. ✅ Create database migrations if needed
3. ✅ Update requirements.txt if needed
4. ✅ Check for breaking changes

### **During Update:**
1. ✅ Monitor deployment logs
2. ✅ Test the updated app
3. ✅ Verify database migrations
4. ✅ Check all functionality

### **After Update:**
1. ✅ Monitor app performance
2. ✅ Check error logs
3. ✅ Verify user functionality
4. ✅ Keep previous version ready for rollback

## 🔄 Automated Updates (Advanced)

### **GitHub Actions (if you want CI/CD):**
```yaml
# .github/workflows/update.yml
name: Update App
on:
  push:
    branches: [ main ]
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Cloud Run
        run: gcloud builds submit --config cloudbuild-simple.yaml .
```

## 💡 Pro Tips

1. **Always test locally first** with Docker Compose
2. **Keep migrations small** and test them
3. **Monitor logs** after each update
4. **Keep a rollback plan** ready
5. **Update during low-traffic hours** if possible

## 🎯 Quick Reference

| What Changed | Command | Migrations? |
|--------------|---------|-------------|
| Code only | `./update-app.sh` | No |
| Models/DB | `./update-app.sh` | Yes |
| Dependencies | `./update-app.sh` | Maybe |
| Config only | `./update-app.sh` | No |

Your app updates are now super simple! 🚀
