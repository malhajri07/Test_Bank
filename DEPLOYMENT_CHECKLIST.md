# Google Cloud Run Deployment Checklist

Quick reference checklist for deploying Exam Stellar to Google Cloud Run.

## Pre-Deployment Checklist

- [ ] Google Cloud account created
- [ ] Google Cloud SDK installed and authenticated
- [ ] Project created in GCP
- [ ] Required APIs enabled (Cloud Run, Cloud SQL, Cloud Build, Storage, Secret Manager)
- [ ] Cloud SQL PostgreSQL instance created
- [ ] Database and user created
- [ ] Cloud Storage bucket created for media files
- [ ] Secrets stored in Secret Manager
- [ ] Service account created with proper permissions
- [ ] Docker image tested locally
- [ ] Environment variables documented

## Deployment Steps

- [ ] **Step 1**: Install Google Cloud SDK
- [ ] **Step 2**: Authenticate and set up project
- [ ] **Step 3**: Set up Cloud SQL PostgreSQL
- [ ] **Step 4**: Set up Cloud Storage bucket
- [ ] **Step 5**: Store secrets in Secret Manager
- [ ] **Step 6**: Update Django settings for production
- [ ] **Step 7**: Create Cloud Run service account
- [ ] **Step 8**: Build and test Docker image locally
- [ ] **Step 9**: Build image in Cloud Build
- [ ] **Step 10**: Deploy to Cloud Run
- [ ] **Step 11**: Configure Cloud SQL connection
- [ ] **Step 12**: Run database migrations
- [ ] **Step 13**: Set up custom domain (optional)
- [ ] **Step 14**: Configure SSL and security headers
- [ ] **Step 15**: Set up CI/CD pipeline (optional)

## Post-Deployment Verification

- [ ] Application accessible via Cloud Run URL
- [ ] Database migrations applied successfully
- [ ] Static files loading correctly
- [ ] Media files uploading to Cloud Storage
- [ ] Admin panel accessible
- [ ] User registration/login working
- [ ] Stripe payments working (if applicable)
- [ ] Email functionality working
- [ ] Logs accessible and error-free
- [ ] Performance acceptable

## Environment Variables Required

```
DB_NAME=testbank_db
DB_USER=django_user
DB_HOST=/cloudsql/PROJECT:REGION:INSTANCE
DB_PORT=5432
DB_PASSWORD=<from-secret-manager>
SECRET_KEY=<from-secret-manager>
DEBUG=False
ALLOWED_HOSTS=your-cloud-run-url.run.app
GS_BUCKET_NAME=exam-stellar-media
USE_CLOUD_STORAGE=True
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=<from-secret-manager>
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<your-password>
```

## Quick Commands Reference

```bash
# Build and deploy
gcloud builds submit --tag us-central1-docker.pkg.dev/PROJECT/REPO/IMAGE:latest
gcloud run deploy exam-stellar --image IMAGE_URL --region us-central1

# View logs
gcloud run services logs read exam-stellar --region us-central1

# Update environment variables
gcloud run services update exam-stellar --region us-central1 --update-env-vars KEY=VALUE

# Get service URL
gcloud run services describe exam-stellar --region us-central1 --format="value(status.url)"
```

