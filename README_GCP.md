# Quick Start: Deploy to Google Cloud Platform

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed: https://cloud.google.com/sdk/docs/install
3. **Docker** installed (for local testing)

## Quick Deployment (5 Steps)

### 1. Initial Setup

```bash
# Set your project ID
export PROJECT_ID=your-project-id
export REGION=us-central1

# Run setup script
chmod +x gcp-setup.sh
./gcp-setup.sh $PROJECT_ID $REGION
```

This creates:
- Cloud SQL PostgreSQL instance
- Cloud Storage buckets
- Secret Manager secrets
- IAM permissions

### 2. Deploy Application

```bash
# Deploy to Cloud Run
chmod +x deploy-cloudrun.sh
./deploy-cloudrun.sh $PROJECT_ID $REGION
```

### 3. Run Migrations

```bash
# Create migration job
gcloud run jobs create migrate \
    --image gcr.io/$PROJECT_ID/exam-stellar:latest \
    --region $REGION \
    --set-env-vars="DB_HOST=/cloudsql/$PROJECT_ID:$REGION:exam-stellar-db,DEBUG=False" \
    --add-cloudsql-instances=$PROJECT_ID:$REGION:exam-stellar-db \
    --set-secrets="SECRET_KEY=django-secret-key:latest,DB_PASSWORD=db-password:latest" \
    --command="python" \
    --args="manage.py,migrate"

# Execute migration
gcloud run jobs execute migrate --region $REGION --wait
```

### 4. Create Superuser

```bash
# Create superuser job
gcloud run jobs create createsuperuser \
    --image gcr.io/$PROJECT_ID/exam-stellar:latest \
    --region $REGION \
    --set-env-vars="DB_HOST=/cloudsql/$PROJECT_ID:$REGION:exam-stellar-db" \
    --add-cloudsql-instances=$PROJECT_ID:$REGION:exam-stellar-db \
    --set-secrets="SECRET_KEY=django-secret-key:latest,DB_PASSWORD=db-password:latest" \
    --command="python" \
    --args="manage.py,createsuperuser"

# Execute (interactive)
gcloud run jobs execute createsuperuser --region $REGION
```

### 5. Access Your Application

```bash
# Get service URL
gcloud run services describe exam-stellar --region $REGION --format="value(status.url)"
```

## Manual Deployment

### Build and Push Image

```bash
gcloud builds submit --tag gcr.io/$PROJECT_ID/exam-stellar:latest
```

### Deploy to Cloud Run

```bash
gcloud run deploy exam-stellar \
    --image gcr.io/$PROJECT_ID/exam-stellar:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars="DB_HOST=/cloudsql/$PROJECT_ID:us-central1:exam-stellar-db,DEBUG=False" \
    --add-cloudsql-instances=$PROJECT_ID:us-central1:exam-stellar-db \
    --set-secrets="SECRET_KEY=django-secret-key:latest,DB_PASSWORD=db-password:latest" \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --min-instances=1
```

## CI/CD with Cloud Build

### Automatic Deployment on Git Push

1. **Connect Repository** (GitHub/Bitbucket)
2. **Create Cloud Build Trigger**:

```bash
gcloud builds triggers create github \
    --name="exam-stellar-deploy" \
    --repo-name="Test_Bank" \
    --repo-owner="malhajri07" \
    --branch-pattern="^main$" \
    --build-config="cloudbuild.yaml"
```

Now every push to `main` branch automatically deploys!

## Environment Variables

Set these in Cloud Run or via Secret Manager:

```bash
# Required
SECRET_KEY=<from-secret-manager>
DB_PASSWORD=<from-secret-manager>
DB_HOST=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
DEBUG=False
ALLOWED_HOSTS=your-domain.com,*.run.app

# Optional
GCP_PROJECT_ID=your-project-id
USE_GCS=True
GCS_BUCKET_NAME=your-project-id-exam-stellar-media
STRIPE_SECRET_KEY=<from-secret-manager>
```

## Monitoring

### View Logs

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=exam-stellar" --limit=50
```

### View Metrics

Visit: https://console.cloud.google.com/run

## Troubleshooting

### Database Connection Issues

```bash
# Check Cloud SQL instance
gcloud sql instances describe exam-stellar-db

# Test connection
gcloud sql connect exam-stellar-db --user=postgres
```

### Static Files Not Loading

```bash
# Re-run collectstatic
gcloud run jobs execute collectstatic --region $REGION
```

### Service Not Starting

```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=exam-stellar" --limit=100
```

## Cost Estimate

**Small-Medium Traffic:**
- Cloud Run: $10-50/month
- Cloud SQL: $25-100/month  
- Cloud Storage: $5-20/month
- **Total: ~$40-170/month**

## Next Steps

See [GCP_DEPLOYMENT.md](GCP_DEPLOYMENT.md) for detailed documentation.

