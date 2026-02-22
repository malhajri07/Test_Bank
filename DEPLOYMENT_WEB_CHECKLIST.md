# Google Cloud Run Deployment - Web Console Checklist

Quick visual checklist for deploying via Google Cloud Web Console.

---

## ✅ Pre-Deployment Setup

- [ ] Google Cloud account created
- [ ] Billing enabled (free tier available)
- [ ] Project created in Google Cloud Console

---

## ✅ Step 1: Create Project

**Location**: Top bar → Project dropdown → NEW PROJECT

- [ ] Project name: `exam-stellar`
- [ ] Project created and selected

---

## ✅ Step 2: Enable APIs

**Location**: ☰ Menu → APIs & Services → Library

Enable these APIs (click each, then ENABLE):

- [ ] Cloud Run API
- [ ] Cloud SQL Admin API
- [ ] Cloud Build API
- [ ] Artifact Registry API
- [ ] Secret Manager API
- [ ] Cloud Storage API

---

## ✅ Step 3: Create Cloud SQL Database

**Location**: ☰ Menu → SQL → CREATE INSTANCE

### Instance Settings:
- [ ] Database type: PostgreSQL
- [ ] Instance ID: `exam-stellar-db`
- [ ] Root password: Created and saved
- [ ] Region: Selected (e.g., `us-central1`)
- [ ] Machine type: `db-f1-micro` (or higher)
- [ ] Storage: 20 GB SSD
- [ ] Public IP: Enabled ✅
- [ ] Instance created (wait 5-10 min)

### Database & User:
- [ ] Database created: `testbank_db`
- [ ] User created: `django_user` with password
- [ ] Connection name copied: `PROJECT:REGION:INSTANCE`

---

## ✅ Step 4: Create Cloud Storage Bucket

**Location**: ☰ Menu → Cloud Storage → Buckets → CREATE

- [ ] Bucket name: `exam-stellar-media`
- [ ] Location: Same as Cloud SQL
- [ ] Storage class: Standard
- [ ] Public access: Enabled (allUsers → Storage Object Viewer)
- [ ] Bucket created

---

## ✅ Step 5: Store Secrets

**Location**: ☰ Menu → Security → Secret Manager → CREATE SECRET

### Django Secret Key:
- [ ] Secret name: `django-secret-key`
- [ ] Secret value: Strong random string
- [ ] Secret created

### Database Password:
- [ ] Secret name: `db-password`
- [ ] Secret value: Database user password
- [ ] Secret created

### Grant Access:
- [ ] `django-secret-key` → Permissions → Grant access to Compute Engine service account
- [ ] `db-password` → Permissions → Grant access to Compute Engine service account
- [ ] Role: Secret Manager Secret Accessor

---

## ✅ Step 6: Create Artifact Registry

**Location**: ☰ Menu → Artifact Registry → CREATE REPOSITORY

- [ ] Repository name: `exam-stellar-repo`
- [ ] Format: Docker
- [ ] Region: Same as Cloud SQL
- [ ] Repository created

---

## ✅ Step 7: Build Docker Image

**Location**: ☰ Menu → Cloud Build → History → RUN

### Option A: Connect Repository
- [ ] Source Repositories → ADD REPOSITORY
- [ ] Connect external repository (GitHub/GitLab)
- [ ] Repository connected

### Option B: Manual Build
- [ ] Cloud Build → RUN → Run manually
- [ ] Upload `cloudbuild.yaml` file
- [ ] Build started

### Create cloudbuild.yaml:
- [ ] File created in project root
- [ ] Content verified (see DEPLOYMENT_WEB_CONSOLE.md)
- [ ] Build completed successfully

---

## ✅ Step 8: Deploy Cloud Run Service

**Location**: ☰ Menu → Cloud Run → CREATE SERVICE

### Basic:
- [ ] Service name: `exam-stellar`
- [ ] Region: Same as Cloud SQL
- [ ] Click NEXT

### Container:
- [ ] Container image: Selected from Artifact Registry
- [ ] Port: `8080`
- [ ] Memory: `2 GiB`
- [ ] CPU: `2`
- [ ] Min instances: `0`
- [ ] Max instances: `10`
- [ ] Timeout: `300 seconds`

### Connections:
- [ ] Cloud SQL connection: Added (`exam-stellar-db`)

### Variables & Secrets:
- [ ] `DB_NAME` = `testbank_db`
- [ ] `DB_USER` = `django_user`
- [ ] `DB_HOST` = `/cloudsql/PROJECT:REGION:exam-stellar-db`
- [ ] `DB_PORT` = `5432`
- [ ] `DEBUG` = `False`
- [ ] `GS_BUCKET_NAME` = `exam-stellar-media`
- [ ] `USE_CLOUD_STORAGE` = `True`
- [ ] `SECRET_KEY` = Secret reference (`django-secret-key`)
- [ ] `DB_PASSWORD` = Secret reference (`db-password`)

### Security:
- [ ] Service account: Compute Engine default
- [ ] Allow unauthenticated: Enabled ✅

### Deploy:
- [ ] Click CREATE
- [ ] Deployment completed
- [ ] Service URL copied: `https://exam-stellar-xxxxx-uc.a.run.app`

---

## ✅ Step 9: Update ALLOWED_HOSTS

**Location**: Cloud Run → exam-stellar → EDIT & DEPLOY NEW REVISION

- [ ] Variables & Secrets tab opened
- [ ] `ALLOWED_HOSTS` updated with service URL
- [ ] New revision deployed

---

## ✅ Step 10: Run Migrations

**Location**: ☰ Menu → Cloud Run → Jobs → CREATE JOB

- [ ] Job name: `migrate-job`
- [ ] Region: Same as service
- [ ] Container image: Same as service
- [ ] Command: `python`
- [ ] Arguments: `manage.py,migrate,--noinput`
- [ ] Cloud SQL connection: Added
- [ ] Environment variables: Same as service
- [ ] Secrets: Same as service
- [ ] Job created
- [ ] Job executed successfully
- [ ] Logs checked (no errors)

---

## ✅ Step 11: Create Superuser

**Location**: Cloud Run → Jobs → CREATE JOB (or use Cloud Shell)

- [ ] Superuser created via job or Cloud Shell
- [ ] Admin credentials saved securely

---

## ✅ Step 12: Verify Deployment

- [ ] Service status: ✅ Healthy
- [ ] Homepage loads: ✅ Working
- [ ] Admin panel accessible: ✅ Working
- [ ] Database connection: ✅ Working
- [ ] Logs checked: ✅ No errors
- [ ] Static files loading: ✅ Working
- [ ] Media uploads working: ✅ Working (if tested)

---

## ✅ Step 13: Custom Domain (Optional)

**Location**: Cloud Run → exam-stellar → MANAGE CUSTOM DOMAINS

- [ ] Domain added: `yourdomain.com`
- [ ] DNS records added
- [ ] Domain verified
- [ ] SSL certificate: Auto-provisioned ✅

---

## ✅ Post-Deployment

- [ ] Monitoring set up
- [ ] Billing alerts configured
- [ ] Backup strategy planned
- [ ] Documentation updated
- [ ] Team notified

---

## 📝 Important Information to Save

### Connection Details:
- **Project ID**: ________________
- **Region**: ________________
- **Cloud SQL Connection Name**: ________________
- **Service URL**: ________________

### Credentials:
- **Database Root Password**: ________________ (stored securely)
- **Database User Password**: ________________ (stored securely)
- **Django Secret Key**: ________________ (stored in Secret Manager)
- **Admin Username**: ________________
- **Admin Password**: ________________

### Resources:
- **Cloud SQL Instance**: `exam-stellar-db`
- **Storage Bucket**: `exam-stellar-media`
- **Artifact Registry**: `exam-stellar-repo`
- **Cloud Run Service**: `exam-stellar`

---

## 🔄 Future Updates

When updating code:

- [ ] Code pushed to repository
- [ ] Cloud Build triggered (or manual build)
- [ ] New image built successfully
- [ ] Cloud Run service updated with new revision
- [ ] Deployment verified
- [ ] Logs checked

---

## 🆘 Troubleshooting Checklist

If service not working:

- [ ] Check Cloud Run logs
- [ ] Verify environment variables
- [ ] Check Cloud SQL connection
- [ ] Verify secrets are accessible
- [ ] Check service account permissions
- [ ] Verify container image exists
- [ ] Check billing is enabled
- [ ] Review error messages in logs

---

## 📊 Monitoring Checklist

Set up monitoring:

- [ ] Cloud Run metrics dashboard reviewed
- [ ] Error rate alerts configured
- [ ] Latency alerts configured
- [ ] Billing alerts configured
- [ ] Log-based alerts set up (optional)

---

**Deployment Date**: _______________

**Deployed By**: _______________

**Status**: ⬜ In Progress | ⬜ Completed | ⬜ Failed


