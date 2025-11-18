# Google Cloud Platform Deployment Guide

This guide covers deploying the Exam Stellar Django application to Google Cloud Platform.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [GCP Services Selection](#gcp-services-selection)
4. [Setup Steps](#setup-steps)
5. [Configuration Files](#configuration-files)
6. [Deployment Options](#deployment-options)
7. [Post-Deployment](#post-deployment)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Cost Optimization](#cost-optimization)
10. [Troubleshooting](#troubleshooting)

## Architecture Overview

### Recommended Architecture

```
┌─────────────────┐
│  Cloud Load     │
│  Balancer       │
│  (HTTPS/SSL)    │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
    ┌────▼────┐      ┌────▼────┐
    │ Cloud    │      │ Cloud   │
    │ Run      │      │ Storage │
    │ (Django) │      │ (Media) │
    └────┬────┘      └─────────┘
         │
    ┌────▼────┐
    │ Cloud SQL│
    │ (Postgres)│
    └─────────┘
```

### Services Used

- **Cloud Run**: Containerized Django application (serverless)
- **Cloud SQL**: Managed PostgreSQL database
- **Cloud Storage**: Media files and static assets
- **Cloud Build**: CI/CD pipeline
- **Cloud Load Balancer**: HTTPS termination and routing
- **Cloud CDN**: Static file delivery
- **Secret Manager**: Secure credential storage
- **Cloud Logging**: Application logs
- **Cloud Monitoring**: Performance metrics

## Prerequisites

1. **Google Cloud Account**
   - Active GCP account with billing enabled
   - Project created in GCP Console

2. **Local Tools**
   - `gcloud` CLI installed and configured
   - Docker installed (for local testing)
   - Git for version control

3. **GCP APIs Enabled**
   - Cloud Run API
   - Cloud SQL Admin API
   - Cloud Storage API
   - Cloud Build API
   - Secret Manager API
   - Cloud Resource Manager API

## GCP Services Selection

### Option 1: Cloud Run (Recommended)

**Pros:**
- Serverless, auto-scaling
- Pay-per-use pricing
- Easy deployment from Docker
- Built-in HTTPS
- No server management

**Cons:**
- Cold start latency (minimal for Django)
- Request timeout limits (60 minutes max)

**Best for:** Most use cases, cost-effective scaling

### Option 2: App Engine Flexible

**Pros:**
- Fully managed platform
- Automatic scaling
- Built-in health checks

**Cons:**
- Less control than Cloud Run
- More expensive than Cloud Run

**Best for:** Traditional PaaS preference

### Option 3: Compute Engine (GKE)

**Pros:**
- Full control
- Kubernetes orchestration
- Best for complex architectures

**Cons:**
- More complex setup
- Requires Kubernetes knowledge
- Higher operational overhead

**Best for:** Large-scale, complex deployments

## Setup Steps

### Step 1: Enable Required APIs

```bash
# Set your project ID
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    storage-component.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    compute.googleapis.com
```

### Step 2: Create Cloud SQL Instance

```bash
# Create PostgreSQL instance
gcloud sql instances create exam-stellar-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=YOUR_SECURE_PASSWORD \
    --storage-type=SSD \
    --storage-size=20GB \
    --backup-start-time=03:00 \
    --enable-bin-log

# Create database
gcloud sql databases create testbank_db --instance=exam-stellar-db

# Create database user
gcloud sql users create django_user \
    --instance=exam-stellar-db \
    --password=YOUR_DB_PASSWORD
```

### Step 3: Create Cloud Storage Bucket

```bash
# Create bucket for media files
gsutil mb -p $PROJECT_ID -l us-central1 gs://exam-stellar-media

# Create bucket for static files (optional, can use Cloud CDN)
gsutil mb -p $PROJECT_ID -l us-central1 gs://exam-stellar-static

# Set bucket permissions
gsutil iam ch allUsers:objectViewer gs://exam-stellar-media
gsutil iam ch allUsers:objectViewer gs://exam-stellar-static
```

### Step 4: Store Secrets in Secret Manager

```bash
# Store Django secret key
echo -n "your-secret-key-here" | gcloud secrets create django-secret-key \
    --data-file=- \
    --replication-policy="automatic"

# Store database password
echo -n "your-db-password" | gcloud secrets create db-password \
    --data-file=- \
    --replication-policy="automatic"

# Store Stripe keys
echo -n "your-stripe-secret-key" | gcloud secrets create stripe-secret-key \
    --data-file=- \
    --replication-policy="automatic"
```

### Step 5: Configure IAM Permissions

```bash
# Grant Cloud Run service account access to secrets
export SERVICE_ACCOUNT=$(gcloud iam service-accounts list --filter="displayName:Cloud Run" --format="value(email)")

gcloud secrets add-iam-policy-binding django-secret-key \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding db-password \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 6: Build and Push Docker Image

```bash
# Configure Docker for GCP
gcloud auth configure-docker

# Build and push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/exam-stellar:latest

# Or use Cloud Build
gcloud builds submit --config cloudbuild.yaml
```

### Step 7: Deploy to Cloud Run

```bash
# Deploy service
gcloud run deploy exam-stellar \
    --image gcr.io/$PROJECT_ID/exam-stellar:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars="DB_HOST=/cloudsql/$PROJECT_ID:us-central1:exam-stellar-db" \
    --add-cloudsql-instances=$PROJECT_ID:us-central1:exam-stellar-db \
    --set-secrets="SECRET_KEY=django-secret-key:latest,DB_PASSWORD=db-password:latest" \
    --memory=1Gi \
    --cpu=1 \
    --timeout=300 \
    --max-instances=10 \
    --min-instances=0
```

## Configuration Files

### cloudbuild.yaml

```yaml
steps:
  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/exam-stellar:$SHORT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/exam-stellar:latest'
      - '.'

  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/exam-stellar:$SHORT_SHA'

  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/exam-stellar:latest'

  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'exam-stellar'
      - '--image'
      - 'gcr.io/$PROJECT_ID/exam-stellar:$SHORT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'

images:
  - 'gcr.io/$PROJECT_ID/exam-stellar:$SHORT_SHA'
  - 'gcr.io/$PROJECT_ID/exam-stellar:latest'

options:
  machineType: 'E2_HIGHCPU_8'
  logging: CLOUD_LOGGING_ONLY

timeout: '1200s'
```

### app.yaml (Alternative: App Engine)

```yaml
runtime: custom
env: flex

runtime_config:
  operating_system: ubuntu
  runtime_version: "18"

resources:
  cpu: 1
  memory_gb: 2
  disk_size_gb: 10

automatic_scaling:
  min_num_instances: 1
  max_num_instances: 10
  cool_down_period_sec: 180
  cpu_utilization:
    target_utilization: 0.6

env_variables:
  DEBUG: 'False'
  DB_HOST: '/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME'
```

### .gcloudignore

```
# Git
.git
.gitignore

# Python
__pycache__/
*.py[cod]
venv/
env/

# Django
*.log
db.sqlite3
/media
/staticfiles

# Environment
.env
.env.local

# IDE
.vscode/
.idea/

# Testing
.pytest_cache/
.benchmarks/

# Node
node_modules/

# Docker
docker-compose*.yml
Dockerfile.dev

# Documentation
*.md
!README.md
```

## Deployment Options

### Option A: Cloud Run (Recommended)

**Deployment Script: `deploy-cloudrun.sh`**

```bash
#!/bin/bash
set -e

PROJECT_ID="your-project-id"
REGION="us-central1"
SERVICE_NAME="exam-stellar"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Build and push
gcloud builds submit --tag $IMAGE_NAME:latest

# Deploy
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="DB_HOST=/cloudsql/$PROJECT_ID:$REGION:exam-stellar-db,DEBUG=False" \
    --add-cloudsql-instances=$PROJECT_ID:$REGION:exam-stellar-db \
    --set-secrets="SECRET_KEY=django-secret-key:latest,DB_PASSWORD=db-password:latest,STRIPE_SECRET_KEY=stripe-secret-key:latest" \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --min-instances=1 \
    --port=8000
```

### Option B: App Engine Flexible

**Deployment:**

```bash
gcloud app deploy app.yaml --version=v1 --promote
```

### Option C: Manual Compute Engine

**Setup VM:**

```bash
# Create VM instance
gcloud compute instances create exam-stellar-vm \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --machine-type=e2-medium \
    --zone=us-central1-a \
    --boot-disk-size=20GB

# SSH and install Docker
gcloud compute ssh exam-stellar-vm --zone=us-central1-a
```

## Post-Deployment

### 1. Run Migrations

```bash
# Connect to Cloud Run service
gcloud run services update exam-stellar \
    --update-env-vars="RUN_MIGRATIONS=true"

# Or run manually
gcloud run jobs create migrate \
    --image gcr.io/$PROJECT_ID/exam-stellar:latest \
    --region us-central1 \
    --set-env-vars="DB_HOST=/cloudsql/$PROJECT_ID:us-central1:exam-stellar-db" \
    --add-cloudsql-instances=$PROJECT_ID:us-central1:exam-stellar-db

gcloud run jobs execute migrate --region us-central1
```

### 2. Create Superuser

```bash
# Create Cloud Run job for superuser creation
gcloud run jobs create createsuperuser \
    --image gcr.io/$PROJECT_ID/exam-stellar:latest \
    --region us-central1 \
    --command="python" \
    --args="manage.py,createsuperuser" \
    --set-env-vars="DB_HOST=/cloudsql/$PROJECT_ID:us-central1:exam-stellar-db" \
    --add-cloudsql-instances=$PROJECT_ID:us-central1:exam-stellar-db

# Execute interactively
gcloud run jobs execute createsuperuser --region us-central1
```

### 3. Collect Static Files

```bash
# Update entrypoint to collect static files (already in docker-entrypoint.sh)
# Or run as Cloud Run job
gcloud run jobs create collectstatic \
    --image gcr.io/$PROJECT_ID/exam-stellar:latest \
    --region us-central1 \
    --command="python" \
    --args="manage.py,collectstatic,--noinput" \
    --set-env-vars="DB_HOST=/cloudsql/$PROJECT_ID:us-central1:exam-stellar-db" \
    --add-cloudsql-instances=$PROJECT_ID:us-central1:exam-stellar-db

gcloud run jobs execute collectstatic --region us-central1
```

### 4. Configure Custom Domain

```bash
# Map custom domain
gcloud run domain-mappings create \
    --service exam-stellar \
    --domain yourdomain.com \
    --region us-central1

# Follow DNS instructions provided
```

### 5. Set Up Cloud CDN

```bash
# Create backend bucket for static files
gcloud compute backend-buckets create exam-stellar-static-backend \
    --gcs-bucket-name=exam-stellar-static

# Create URL map
gcloud compute url-maps create exam-stellar-map \
    --default-backend-bucket=exam-stellar-static-backend

# Create HTTPS proxy
gcloud compute target-https-proxies create exam-stellar-https-proxy \
    --url-map=exam-stellar-map \
    --ssl-certificates=your-ssl-cert

# Create forwarding rule
gcloud compute forwarding-rules create exam-stellar-https-rule \
    --global \
    --target-https-proxy=exam-stellar-https-proxy \
    --ports=443
```

## Monitoring & Maintenance

### Cloud Logging

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=exam-stellar" --limit=50

# Stream logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=exam-stellar"
```

### Cloud Monitoring

- Set up alerts for error rates
- Monitor response times
- Track database connections
- Monitor Cloud SQL performance

### Backup Strategy

```bash
# Automated backups (configured in Cloud SQL)
# Manual backup
gcloud sql export sql exam-stellar-db gs://exam-stellar-backups/backup-$(date +%Y%m%d).sql \
    --database=testbank_db

# Restore from backup
gcloud sql import sql exam-stellar-db gs://exam-stellar-backups/backup-20231119.sql \
    --database=testbank_db
```

## Cost Optimization

### Cloud Run Optimization

- **Min instances**: Set to 0 for development, 1 for production
- **Max instances**: Limit based on expected traffic
- **Memory**: Start with 1Gi, adjust based on usage
- **CPU**: Use 1 CPU for most cases, scale up if needed
- **Timeout**: Set appropriate timeout (300s default)

### Cloud SQL Optimization

- **Instance tier**: Start with db-f1-micro for dev, db-n1-standard-1 for prod
- **Storage**: Use SSD for better performance
- **Backups**: Configure automated backups (retention: 7 days)
- **High Availability**: Enable for production

### Cloud Storage Optimization

- **Storage class**: Use Standard for frequently accessed files
- **Lifecycle policies**: Move old files to Nearline/Coldline
- **CDN**: Use Cloud CDN for static files

### Estimated Monthly Costs (Small-Medium Traffic)

- **Cloud Run**: $10-50/month (pay-per-use)
- **Cloud SQL**: $25-100/month (db-f1-micro to db-n1-standard-1)
- **Cloud Storage**: $5-20/month (depends on media volume)
- **Cloud CDN**: $10-30/month (traffic-based)
- **Total**: ~$50-200/month

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify Cloud SQL instance is running
   - Check Cloud SQL connection name format
   - Verify service account permissions

2. **Static Files Not Loading**
   - Run `collectstatic` after deployment
   - Check Cloud Storage bucket permissions
   - Verify STATIC_ROOT configuration

3. **Media Files Not Uploading**
   - Check Cloud Storage bucket permissions
   - Verify MEDIA_ROOT configuration
   - Check IAM roles for Cloud Run service account

4. **High Latency**
   - Enable Cloud CDN for static files
   - Use Cloud SQL connection pooling
   - Optimize database queries

5. **Cold Start Issues**
   - Set min-instances=1 for production
   - Optimize Docker image size
   - Use Cloud Run warm-up requests

## Security Best Practices

1. **Secrets Management**
   - Use Secret Manager for all sensitive data
   - Never commit secrets to repository
   - Rotate secrets regularly

2. **Network Security**
   - Use Cloud SQL private IP (recommended)
   - Enable VPC connector for private networking
   - Configure firewall rules

3. **Application Security**
   - Set DEBUG=False in production
   - Configure ALLOWED_HOSTS properly
   - Enable CSRF protection
   - Use HTTPS only

4. **Database Security**
   - Use strong passwords
   - Enable SSL for database connections
   - Restrict database access to Cloud Run only
   - Regular security updates

5. **IAM Best Practices**
   - Use least privilege principle
   - Separate service accounts for different services
   - Regular access reviews

## Next Steps

1. Set up CI/CD pipeline with Cloud Build
2. Configure custom domain and SSL certificate
3. Set up monitoring alerts
4. Configure automated backups
5. Set up staging environment
6. Implement blue-green deployments
7. Configure auto-scaling policies
8. Set up cost alerts and budgets

