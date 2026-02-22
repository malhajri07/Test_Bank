# Google Cloud Run Deployment - Step-by-Step Summary

## All Steps Required for Deployment

### Step 1: Install Google Cloud SDK
```bash
# macOS
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Linux
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt-get update && sudo apt-get install google-cloud-sdk
gcloud init
```

### Step 2: Authenticate and Create Project
```bash
gcloud auth login
gcloud projects create exam-stellar --name="Exam Stellar Platform"
gcloud config set project exam-stellar
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable storage-component.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### Step 3: Create Cloud SQL PostgreSQL Database
```bash
gcloud sql instances create exam-stellar-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=YOUR_SECURE_PASSWORD_HERE

gcloud sql databases create testbank_db --instance=exam-stellar-db
gcloud sql users create django_user \
    --instance=exam-stellar-db \
    --password=YOUR_DB_USER_PASSWORD_HERE

# Save connection name
CONNECTION_NAME=$(gcloud sql instances describe exam-stellar-db --format="value(connectionName)")
echo $CONNECTION_NAME
```

### Step 4: Create Cloud Storage Bucket for Media Files
```bash
gsutil mb -p exam-stellar -c STANDARD -l us-central1 gs://exam-stellar-media
gsutil iam ch allUsers:objectViewer gs://exam-stellar-media
```

### Step 5: Store Secrets in Secret Manager
```bash
echo -n "your-django-secret-key-here" | gcloud secrets create django-secret-key --data-file=-
echo -n "YOUR_DB_USER_PASSWORD_HERE" | gcloud secrets create db-password --data-file=-

PROJECT_NUMBER=$(gcloud projects describe exam-stellar --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding django-secret-key \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
gcloud secrets add-iam-policy-binding db-password \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 6: Create Service Account (Optional but Recommended)
```bash
gcloud iam service-accounts create cloud-run-sa \
    --display-name="Cloud Run Service Account"

gcloud projects add-iam-policy-binding exam-stellar \
    --member="serviceAccount:cloud-run-sa@exam-stellar.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding exam-stellar \
    --member="serviceAccount:cloud-run-sa@exam-stellar.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"
```

### Step 7: Create Artifact Registry Repository
```bash
gcloud artifacts repositories create exam-stellar-repo \
    --repository-format=docker \
    --location=us-central1
```

### Step 8: Build Docker Image
```bash
cd /Users/mohammedalhajri/Test_Bank
gcloud builds submit --tag us-central1-docker.pkg.dev/exam-stellar/exam-stellar-repo/exam-stellar:latest
```

### Step 9: Deploy to Cloud Run
```bash
CONNECTION_NAME=$(gcloud sql instances describe exam-stellar-db --format="value(connectionName)")

gcloud run deploy exam-stellar \
    --image us-central1-docker.pkg.dev/exam-stellar/exam-stellar-repo/exam-stellar:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --add-cloudsql-instances $CONNECTION_NAME \
    --set-env-vars="DB_NAME=testbank_db,DB_USER=django_user,DB_HOST=/cloudsql/$CONNECTION_NAME,DB_PORT=5432,DEBUG=False" \
    --set-secrets="DB_PASSWORD=db-password:latest,SECRET_KEY=django-secret-key:latest" \
    --set-env-vars="ALLOWED_HOSTS=exam-stellar-xxxxx-uc.a.run.app,GS_BUCKET_NAME=exam-stellar-media,USE_CLOUD_STORAGE=True" \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --service-account cloud-run-sa@exam-stellar.iam.gserviceaccount.com
```

**Note:** Replace `exam-stellar-xxxxx-uc.a.run.app` with your actual Cloud Run URL after first deployment.

### Step 10: Get Service URL and Update ALLOWED_HOSTS
```bash
SERVICE_URL=$(gcloud run services describe exam-stellar --region us-central1 --format="value(status.url)")
echo "Service URL: $SERVICE_URL"

# Update ALLOWED_HOSTS with actual URL
gcloud run services update exam-stellar \
    --region us-central1 \
    --update-env-vars="ALLOWED_HOSTS=$SERVICE_URL"
```

### Step 11: Run Database Migrations
```bash
CONNECTION_NAME=$(gcloud sql instances describe exam-stellar-db --format="value(connectionName)")

gcloud run jobs create migrate-job \
    --image us-central1-docker.pkg.dev/exam-stellar/exam-stellar-repo/exam-stellar:latest \
    --region us-central1 \
    --add-cloudsql-instances $CONNECTION_NAME \
    --set-env-vars="DB_NAME=testbank_db,DB_USER=django_user,DB_HOST=/cloudsql/$CONNECTION_NAME" \
    --set-secrets="DB_PASSWORD=db-password:latest,SECRET_KEY=django-secret-key:latest" \
    --command="python" \
    --args="manage.py,migrate,--noinput" \
    --max-retries 3

gcloud run jobs execute migrate-job --region us-central1
```

### Step 12: Create Superuser (One-time)
```bash
# Option 1: Via Cloud Run job
gcloud run jobs create createsuperuser-job \
    --image us-central1-docker.pkg.dev/exam-stellar/exam-stellar-repo/exam-stellar:latest \
    --region us-central1 \
    --add-cloudsql-instances $CONNECTION_NAME \
    --set-env-vars="DB_NAME=testbank_db,DB_USER=django_user,DB_HOST=/cloudsql/$CONNECTION_NAME" \
    --set-secrets="DB_PASSWORD=db-password:latest,SECRET_KEY=django-secret-key:latest" \
    --command="python" \
    --args="manage.py,shell" \
    --max-retries 1

# Option 2: Via Django shell (interactive)
gcloud run services update exam-stellar \
    --region us-central1 \
    --update-env-vars="CREATE_SUPERUSER=true"

# Then access the service and create superuser manually
```

### Step 13: Verify Deployment
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe exam-stellar --region us-central1 --format="value(status.url)")
echo "Visit: $SERVICE_URL"

# Check logs
gcloud run services logs read exam-stellar --region us-central1 --limit 50

# Check service status
gcloud run services describe exam-stellar --region us-central1
```

### Step 14: Update Code and Redeploy (Future Updates)
```bash
# Make code changes, then:
git add .
git commit -m "Update application"
git push origin main

# Rebuild and redeploy
gcloud builds submit --tag us-central1-docker.pkg.dev/exam-stellar/exam-stellar-repo/exam-stellar:latest
gcloud run deploy exam-stellar \
    --image us-central1-docker.pkg.dev/exam-stellar/exam-stellar-repo/exam-stellar:latest \
    --region us-central1
```

---

## Important Environment Variables

Set these in Cloud Run (via `--set-env-vars` or Cloud Console):

```
DB_NAME=testbank_db
DB_USER=django_user
DB_HOST=/cloudsql/PROJECT:REGION:INSTANCE
DB_PORT=5432
DEBUG=False
GS_BUCKET_NAME=exam-stellar-media
USE_CLOUD_STORAGE=True
ALLOWED_HOSTS=your-service-url.run.app
```

Set these as secrets (via `--set-secrets`):

```
DB_PASSWORD=db-password:latest
SECRET_KEY=django-secret-key:latest
```

Optional (set as env vars or secrets):

```
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=stripe-secret-key:latest
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password
```

---

## Quick Troubleshooting

```bash
# View recent logs
gcloud run services logs read exam-stellar --region us-central1 --limit 100

# Stream logs
gcloud run services logs tail exam-stellar --region us-central1

# Check service configuration
gcloud run services describe exam-stellar --region us-central1

# Update environment variable
gcloud run services update exam-stellar \
    --region us-central1 \
    --update-env-vars KEY=VALUE

# Scale service
gcloud run services update exam-stellar \
    --region us-central1 \
    --min-instances 1 \
    --max-instances 10
```

---

## Cost Estimate (Approximate)

- **Cloud Run**: ~$0.40 per million requests (first 2 million free)
- **Cloud SQL (db-f1-micro)**: ~$7-10/month
- **Cloud Storage**: ~$0.020 per GB/month
- **Cloud Build**: First 120 build-minutes/day free
- **Secret Manager**: First 6 secrets free

**Total estimated cost**: ~$10-20/month for low traffic

---

## Next Steps After Deployment

1. Set up custom domain
2. Configure SSL certificates
3. Set up monitoring and alerts
4. Configure backup strategy
5. Set up CI/CD pipeline
6. Configure CDN for static files
7. Set up staging environment


