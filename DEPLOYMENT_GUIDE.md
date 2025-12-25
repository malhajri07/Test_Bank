# Google Cloud Run Deployment Guide

Complete step-by-step guide to deploy Exam Stellar Django application to Google Cloud Run using Docker.

## Prerequisites

- Google Cloud Platform account (sign up at https://cloud.google.com)
- Google Cloud SDK (gcloud CLI) installed
- Docker installed locally (for testing)
- Git repository pushed to GitHub/GitLab
- PostgreSQL database (Cloud SQL recommended)

---

## Step 1: Install Google Cloud SDK

### For macOS:
```bash
# Download and install
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize gcloud
gcloud init
```

### For Linux:
```bash
# Add Cloud SDK repository
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

# Install
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt-get update && sudo apt-get install google-cloud-sdk

# Initialize
gcloud init
```

### For Windows:
1. Download installer from: https://cloud.google.com/sdk/docs/install
2. Run the installer
3. Open Cloud SDK Shell and run: `gcloud init`

---

## Step 2: Authenticate and Set Up Project

```bash
# Login to Google Cloud
gcloud auth login

# Create a new project (or use existing)
gcloud projects create exam-stellar --name="Exam Stellar Platform"

# Set the project as active
gcloud config set project exam-stellar

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable storage-component.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

---

## Step 3: Set Up Cloud SQL PostgreSQL Database

```bash
# Create Cloud SQL instance (choose region closest to your users)
gcloud sql instances create exam-stellar-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=YOUR_SECURE_PASSWORD_HERE

# Create database
gcloud sql databases create testbank_db --instance=exam-stellar-db

# Create database user
gcloud sql users create django_user \
    --instance=exam-stellar-db \
    --password=YOUR_DB_USER_PASSWORD_HERE

# Get connection name (you'll need this later)
gcloud sql instances describe exam-stellar-db --format="value(connectionName)"
# Save this output, it looks like: project-id:region:instance-name
```

**Note:** For production, use a higher tier (e.g., `db-n1-standard-1` or higher).

---

## Step 4: Set Up Cloud Storage for Media Files

```bash
# Create storage bucket for media files
gsutil mb -p exam-stellar -c STANDARD -l us-central1 gs://exam-stellar-media

# Make bucket publicly readable (for media files)
gsutil iam ch allUsers:objectViewer gs://exam-stellar-media

# Optional: Set lifecycle policy to delete old files
gsutil lifecycle set lifecycle.json gs://exam-stellar-media
```

Create `lifecycle.json`:
```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 365}
      }
    ]
  }
}
```

---

## Step 5: Store Secrets in Secret Manager

```bash
# Store Django secret key
echo -n "your-super-secret-django-key-here" | gcloud secrets create django-secret-key --data-file=-

# Store database password
echo -n "YOUR_DB_USER_PASSWORD_HERE" | gcloud secrets create db-password --data-file=-

# Store Stripe keys (if using)
echo -n "sk_live_..." | gcloud secrets create stripe-secret-key --data-file=-
echo -n "pk_live_..." | gcloud secrets create stripe-public-key --data-file=-

# Grant Cloud Run service account access to secrets
PROJECT_NUMBER=$(gcloud projects describe exam-stellar --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding django-secret-key \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
gcloud secrets add-iam-policy-binding db-password \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

---

## Step 6: Update Django Settings for Production

Update `testbank_platform/settings.py` to add Cloud Storage and Secret Manager support:

```python
# Add at the top of settings.py
import os
from google.cloud import secretmanager

def get_secret(secret_id):
    """Retrieve secret from Google Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{os.environ.get('GOOGLE_CLOUD_PROJECT', 'exam-stellar')}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception:
        # Fallback to environment variable
        return os.environ.get(secret_id, '')

# Update SECRET_KEY
SECRET_KEY = get_secret('django-secret-key') or config('SECRET_KEY', default='...')

# Update DEBUG and ALLOWED_HOSTS
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=lambda v: [s.strip() for s in v.split(',')])

# Add Cloud Storage for media files (if using)
if config('USE_CLOUD_STORAGE', default=False, cast=bool):
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    GS_BUCKET_NAME = config('GS_BUCKET_NAME', default='exam-stellar-media')
    GS_DEFAULT_ACL = 'publicRead'
    MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'
```

---

## Step 7: Create Cloud Run Service Account (Optional but Recommended)

```bash
# Create service account
gcloud iam service-accounts create cloud-run-sa \
    --display-name="Cloud Run Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding exam-stellar \
    --member="serviceAccount:cloud-run-sa@exam-stellar.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding exam-stellar \
    --member="serviceAccount:cloud-run-sa@exam-stellar.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"
```

---

## Step 8: Build and Test Docker Image Locally

```bash
# Navigate to project directory
cd /Users/mohammedalhajri/Test_Bank

# Build Docker image
docker build -t exam-stellar:latest .

# Test locally (optional - requires local PostgreSQL)
docker run -p 8080:8080 \
    -e DB_HOST=your-db-host \
    -e DB_NAME=testbank_db \
    -e DB_USER=django_user \
    -e DB_PASSWORD=your-password \
    -e SECRET_KEY=test-key \
    -e DEBUG=False \
    -e ALLOWED_HOSTS=localhost \
    exam-stellar:latest
```

---

## Step 9: Configure Cloud Build and Build Image

```bash
# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# Build and push image to Container Registry
gcloud builds submit --tag gcr.io/exam-stellar/exam-stellar:latest

# Or use Artifact Registry (recommended)
gcloud artifacts repositories create exam-stellar-repo \
    --repository-format=docker \
    --location=us-central1

# Build and push to Artifact Registry
gcloud builds submit --tag us-central1-docker.pkg.dev/exam-stellar/exam-stellar-repo/exam-stellar:latest
```

---

## Step 10: Deploy to Cloud Run

```bash
# Get Cloud SQL connection name
CONNECTION_NAME=$(gcloud sql instances describe exam-stellar-db --format="value(connectionName)")

# Deploy to Cloud Run
gcloud run deploy exam-stellar \
    --image us-central1-docker.pkg.dev/exam-stellar/exam-stellar-repo/exam-stellar:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --add-cloudsql-instances $CONNECTION_NAME \
    --set-env-vars="DB_NAME=testbank_db,DB_USER=django_user,DB_HOST=/cloudsql/$CONNECTION_NAME,DB_PORT=5432" \
    --set-secrets="DB_PASSWORD=db-password:latest,SECRET_KEY=django-secret-key:latest" \
    --set-env-vars="DEBUG=False,ALLOWED_HOSTS=exam-stellar-xxxxx-uc.a.run.app" \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --service-account cloud-run-sa@exam-stellar.iam.gserviceaccount.com
```

**Important Environment Variables to Set:**
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_HOST`: Cloud SQL connection path (`/cloudsql/PROJECT:REGION:INSTANCE`)
- `DB_PORT`: `5432`
- `SECRET_KEY`: From Secret Manager
- `DEBUG`: `False`
- `ALLOWED_HOSTS`: Your Cloud Run URL
- `GS_BUCKET_NAME`: `exam-stellar-media` (if using Cloud Storage)
- `USE_CLOUD_STORAGE`: `True` (if using Cloud Storage)
- `STRIPE_PUBLIC_KEY`: Your Stripe public key
- `STRIPE_SECRET_KEY`: From Secret Manager
- `EMAIL_HOST`: Your SMTP host
- `EMAIL_HOST_USER`: Your email
- `EMAIL_HOST_PASSWORD`: Your email password

---

## Step 11: Configure Cloud SQL Connection

After deployment, you need to ensure Cloud Run can connect to Cloud SQL:

```bash
# The --add-cloudsql-instances flag in Step 10 should handle this
# But verify the connection name is correct

# Check Cloud Run service configuration
gcloud run services describe exam-stellar --region us-central1 --format="value(spec.template.spec.containers[0].env)"
```

---

## Step 12: Run Database Migrations

```bash
# Get Cloud Run service URL
SERVICE_URL=$(gcloud run services describe exam-stellar --region us-central1 --format="value(status.url)")

# Run migrations via Cloud Run job or exec
gcloud run jobs create migrate-job \
    --image us-central1-docker.pkg.dev/exam-stellar/exam-stellar-repo/exam-stellar:latest \
    --region us-central1 \
    --add-cloudsql-instances $CONNECTION_NAME \
    --set-env-vars="DB_NAME=testbank_db,DB_USER=django_user,DB_HOST=/cloudsql/$CONNECTION_NAME" \
    --set-secrets="DB_PASSWORD=db-password:latest,SECRET_KEY=django-secret-key:latest" \
    --command="python" \
    --args="manage.py,migrate" \
    --max-retries 3

# Execute the migration job
gcloud run jobs execute migrate-job --region us-central1

# Or create superuser (one-time)
gcloud run jobs create createsuperuser-job \
    --image us-central1-docker.pkg.dev/exam-stellar/exam-stellar-repo/exam-stellar:latest \
    --region us-central1 \
    --add-cloudsql-instances $CONNECTION_NAME \
    --set-env-vars="DB_NAME=testbank_db,DB_USER=django_user,DB_HOST=/cloudsql/$CONNECTION_NAME,CREATE_SUPERUSER=true" \
    --set-secrets="DB_PASSWORD=db-password:latest,SECRET_KEY=django-secret-key:latest" \
    --command="python" \
    --args="manage.py,createsuperuser,--noinput,--username,admin,--email,admin@example.com" \
    --max-retries 1

# Note: For superuser, you'll need to set password via environment variable or use Django shell
```

---

## Step 13: Set Up Custom Domain (Optional)

```bash
# Map custom domain to Cloud Run service
gcloud run domain-mappings create \
    --service exam-stellar \
    --domain yourdomain.com \
    --region us-central1

# Follow instructions to verify domain ownership
# Add DNS records as instructed
```

---

## Step 14: Configure SSL and Security Headers

Update `settings.py` for production security:

```python
# Security Settings (uncomment for production)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

---

## Step 15: Set Up CI/CD Pipeline (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - id: 'auth'
        uses: 'google-github-actions/auth@v1'
        with:
          credentials_json: '${{ secrets.GCP_SA_KEY }}'
      
      - name: 'Set up Cloud SDK'
        uses: 'google-github-actions/setup-gcloud@v1'
      
      - name: 'Build and Push'
        run: |
          gcloud builds submit --tag us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT }}/exam-stellar-repo/exam-stellar:${{ github.sha }}
      
      - name: 'Deploy'
        run: |
          gcloud run deploy exam-stellar \
            --image us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT }}/exam-stellar-repo/exam-stellar:${{ github.sha }} \
            --region us-central1 \
            --platform managed
```

---

## Step 16: Monitor and Logs

```bash
# View logs
gcloud run services logs read exam-stellar --region us-central1 --limit 50

# Stream logs in real-time
gcloud run services logs tail exam-stellar --region us-central1

# View service details
gcloud run services describe exam-stellar --region us-central1
```

---

## Step 17: Update Deployment

```bash
# After making code changes, rebuild and redeploy
git add .
git commit -m "Update application"
git push origin main

# If using CI/CD, deployment happens automatically
# Otherwise, manually rebuild and deploy:
gcloud builds submit --tag us-central1-docker.pkg.dev/exam-stellar/exam-stellar-repo/exam-stellar:latest
gcloud run deploy exam-stellar \
    --image us-central1-docker.pkg.dev/exam-stellar/exam-stellar-repo/exam-stellar:latest \
    --region us-central1
```

---

## Troubleshooting

### Database Connection Issues
```bash
# Check Cloud SQL instance status
gcloud sql instances describe exam-stellar-db

# Verify connection name format
gcloud sql instances describe exam-stellar-db --format="value(connectionName)"
```

### Static Files Not Loading
- Ensure `collectstatic` runs in docker-entrypoint.sh
- Check `STATIC_ROOT` and `STATIC_URL` settings
- Verify Cloud Storage bucket permissions (if using)

### Media Files Not Uploading
- Verify Cloud Storage bucket exists and is accessible
- Check `GS_BUCKET_NAME` environment variable
- Ensure service account has `storage.objectCreator` role

### Application Crashes
```bash
# Check logs
gcloud run services logs read exam-stellar --region us-central1 --limit 100

# Check service status
gcloud run services describe exam-stellar --region us-central1
```

### Environment Variables Not Working
- Verify secrets exist: `gcloud secrets list`
- Check service account permissions
- Ensure environment variables are set correctly in Cloud Run

---

## Cost Optimization Tips

1. **Use Cloud SQL Proxy**: Already configured via `--add-cloudsql-instances`
2. **Set Min Instances to 0**: Reduces costs when no traffic
3. **Use Appropriate Instance Sizes**: Start with `--memory 2Gi --cpu 2`
4. **Enable Cloud CDN**: For static files caching
5. **Use Cloud Storage Lifecycle Policies**: Auto-delete old media files

---

## Quick Reference Commands

```bash
# View service URL
gcloud run services describe exam-stellar --region us-central1 --format="value(status.url)"

# Update environment variable
gcloud run services update exam-stellar \
    --region us-central1 \
    --update-env-vars KEY=VALUE

# Scale service
gcloud run services update exam-stellar \
    --region us-central1 \
    --min-instances 1 \
    --max-instances 10

# Delete service (if needed)
gcloud run services delete exam-stellar --region us-central1
```

---

## Next Steps

1. Set up monitoring with Cloud Monitoring
2. Configure alerts for errors and performance
3. Set up backup strategy for Cloud SQL
4. Configure CDN for static assets
5. Set up staging environment
6. Implement health check endpoints
7. Configure rate limiting
8. Set up error tracking (Sentry, etc.)

---

## Support Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)

