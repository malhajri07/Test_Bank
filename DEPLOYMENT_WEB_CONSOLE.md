# Google Cloud Run Deployment - Web Console Guide

Complete step-by-step guide to deploy Exam Stellar Django application to Google Cloud Run using the Google Cloud Web Console (no command line required).

---

## Prerequisites

- Google Cloud Platform account (sign up at https://cloud.google.com)
- Credit card for billing (free tier available)
- Docker image built and ready (or we'll use Cloud Build)
- GitHub/GitLab repository (optional, for CI/CD)

---

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top (next to "Google Cloud")
3. Click **"NEW PROJECT"**
4. Enter project details:
   - **Project name**: `exam-stellar` (or your preferred name)
   - **Organization**: Select your organization (if applicable)
   - **Location**: Select your organization folder (if applicable)
5. Click **"CREATE"**
6. Wait for project creation (takes a few seconds)
7. Select your new project from the dropdown

---

## Step 2: Enable Required APIs

1. In the Google Cloud Console, click the **☰ (hamburger menu)** at the top left
2. Go to **"APIs & Services"** → **"Library"**
3. Search for and enable each of these APIs (click on each, then click "ENABLE"):

   **a. Cloud Run API**
   - Search: `Cloud Run API`
   - Click on it
   - Click **"ENABLE"**

   **b. Cloud SQL Admin API**
   - Search: `Cloud SQL Admin API`
   - Click on it
   - Click **"ENABLE"**

   **c. Cloud Build API**
   - Search: `Cloud Build API`
   - Click on it
   - Click **"ENABLE"**

   **d. Artifact Registry API**
   - Search: `Artifact Registry API`
   - Click on it
   - Click **"ENABLE"**

   **e. Secret Manager API**
   - Search: `Secret Manager API`
   - Click on it
   - Click **"ENABLE"**

   **f. Cloud Storage API**
   - Search: `Cloud Storage API`
   - Click on it
   - Click **"ENABLE"**

---

## Step 3: Create Cloud SQL PostgreSQL Database

1. Click **☰ (hamburger menu)** → **"SQL"**
2. Click **"CREATE INSTANCE"**
3. Choose **"PostgreSQL"** → Click **"NEXT"**
4. Fill in instance details:
   - **Instance ID**: `exam-stellar-db`
   - **Root password**: Create a strong password (save it securely!)
   - **Database version**: `PostgreSQL 14` (or latest)
   - **Region**: Choose closest to your users (e.g., `us-central1`)
   - **Zone**: Leave as default or select specific zone
5. Click **"SHOW CONFIGURATION OPTIONS"**
6. Under **"Machine type"**:
   - Select **"Lightweight"** or **"Shared-core"**
   - Choose **"db-f1-micro"** (for testing) or **"db-n1-standard-1"** (for production)
7. Under **"Storage"**:
   - **Storage type**: `SSD`
   - **Storage capacity**: `20 GB` (minimum)
8. Under **"Backup"**:
   - Enable **"Automated backups"** (recommended)
   - **Backup window**: Leave default or select preferred time
9. Under **"Connections"**:
   - **Public IP**: ✅ Enable (required for Cloud Run)
   - **Private IP**: Optional (for VPC)
10. Click **"CREATE"**
11. Wait 5-10 minutes for instance creation

### Create Database and User

1. Once instance is created, click on **"exam-stellar-db"**
2. Go to **"DATABASES"** tab
3. Click **"CREATE DATABASE"**
   - **Database name**: `testbank_db`
   - Click **"CREATE"**
4. Go to **"USERS"** tab
5. Click **"ADD USER ACCOUNT"**
   - **Username**: `django_user`
   - **Password**: Create a strong password (save it!)
   - Click **"ADD"**
6. Go to **"OVERVIEW"** tab
7. Find **"Connection name"** (format: `project-id:region:instance-name`)
   - **Copy this connection name** - you'll need it later!

---

## Step 4: Create Cloud Storage Bucket for Media Files

1. Click **☰ (hamburger menu)** → **"Cloud Storage"** → **"Buckets"**
2. Click **"CREATE"**
3. Fill in bucket details:
   - **Name**: `exam-stellar-media` (must be globally unique)
   - **Location type**: `Region`
   - **Location**: Same region as your Cloud SQL (e.g., `us-central1`)
   - **Storage class**: `Standard`
   - **Access control**: `Uniform`
4. Click **"CREATE"**
5. Click on the bucket name to open it
6. Go to **"PERMISSIONS"** tab
7. Click **"GRANT ACCESS"**
   - **New principals**: `allUsers`
   - **Role**: `Storage Object Viewer`
   - Click **"SAVE"**
   - Confirm by clicking **"ALLOW PUBLIC ACCESS"**

---

## Step 5: Store Secrets in Secret Manager

### Store Django Secret Key

1. Click **☰ (hamburger menu)** → **"Security"** → **"Secret Manager"**
2. Click **"CREATE SECRET"**
3. Fill in:
   - **Name**: `django-secret-key`
   - **Secret value**: Paste your Django secret key (generate a strong random string)
   - Click **"CREATE SECRET"**

### Store Database Password

1. Click **"CREATE SECRET"** again
2. Fill in:
   - **Name**: `db-password`
   - **Secret value**: Paste the database password you created for `django_user`
   - Click **"CREATE SECRET"**

### Grant Access to Cloud Run Service Account

1. Click on **"django-secret-key"** secret
2. Go to **"PERMISSIONS"** tab
3. Click **"GRANT ACCESS"**
4. In the search box, type: `cloud-run` or your project number
5. Select: `Compute Engine default service account` (format: `PROJECT_NUMBER-compute@developer.gserviceaccount.com`)
6. Role: `Secret Manager Secret Accessor`
7. Click **"SAVE"**
8. Repeat for **"db-password"** secret

---

## Step 6: Create Artifact Registry Repository

1. Click **☰ (hamburger menu)** → **"Artifact Registry"**
2. Click **"CREATE REPOSITORY"**
3. Fill in:
   - **Name**: `exam-stellar-repo`
   - **Format**: `Docker`
   - **Mode**: `Standard`
   - **Region**: Same as your Cloud SQL (e.g., `us-central1`)
4. Click **"CREATE"**

---

## Step 7: Build Docker Image Using Cloud Build

### Option A: Build from Source Code (Recommended)

1. Click **☰ (hamburger menu)** → **"Cloud Build"** → **"Triggers"**
2. Click **"CREATE TRIGGER"**
3. Fill in trigger details:
   - **Name**: `exam-stellar-build`
   - **Event**: `Push to a branch`
   - **Source**: Connect your repository (GitHub/GitLab) or use **"Cloud Source Repositories"**
   - **Branch**: `^main$` (or your main branch)
   - **Configuration**: `Cloud Build configuration file (yaml or json)`
   - **Location**: `cloudbuild.yaml` (we'll create this)
4. Click **"CREATE"**

### Option B: Build Manually from Cloud Source Repositories

1. Click **☰ (hamburger menu)** → **"Source Repositories"**
2. Click **"ADD REPOSITORY"**
3. Select **"Connect external repository"**
4. Choose your Git provider (GitHub/GitLab/Bitbucket)
5. Authenticate and select your repository
6. Click **"CONNECT"**
7. Go to **"Cloud Build"** → **"History"**
8. Click **"RUN"** → **"Run trigger"** or **"Run manually"**

### Create cloudbuild.yaml File

Create a file named `cloudbuild.yaml` in your project root:

```yaml
steps:
  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:$SHORT_SHA', '.']
  
  # Push to Artifact Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:$SHORT_SHA']
  
  # Tag as latest
  - name: 'gcr.io/cloud-builders/docker'
    args: ['tag', 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:$SHORT_SHA', 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:latest']
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:latest']

images:
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:$SHORT_SHA'
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:latest'
```

### Option C: Build from Local Files (One-time Manual Build)

1. Click **☰ (hamburger menu)** → **"Cloud Build"** → **"History"**
2. Click **"RUN"** → **"Run manually"**
3. Fill in:
   - **Source**: `Cloud Source Repositories` or upload files
   - **Configuration**: `Cloud Build configuration file`
   - **Cloud Build configuration file location**: `cloudbuild.yaml`
4. Click **"RUN"**

---

## Step 8: Create Cloud Run Service

1. Click **☰ (hamburger menu)** → **"Cloud Run"**
2. Click **"CREATE SERVICE"**

### Basic Configuration

1. **Service name**: `exam-stellar`
2. **Region**: Same as your Cloud SQL (e.g., `us-central1`)
3. Click **"NEXT"**

### Container Configuration

1. **Container image URL**: 
   - Click **"SELECT"**
   - Choose **"Artifact Registry"**
   - Select repository: `exam-stellar-repo`
   - Select image: `exam-stellar:latest`
   - Click **"SELECT"**

2. **Container port**: `8080`

3. **CPU allocation**: `CPU is only allocated during request processing`

4. **Memory**: `2 GiB`

5. **CPU**: `2`

6. **Minimum number of instances**: `0` (to save costs)

7. **Maximum number of instances**: `10`

8. **Request timeout**: `300 seconds`

9. **Concurrency**: `80` (default)

10. **Maximum requests per container**: `80` (default)

### Connections Tab

1. Click **"CONNECTIONS"** tab
2. Under **"Cloud SQL connections"**:
   - Click **"ADD CLOUD SQL CONNECTION"**
   - Select your instance: `exam-stellar-db`
   - Click **"DONE"**

### Variables & Secrets Tab

1. Click **"VARIABLES & SECRETS"** tab

2. **Environment variables** - Click **"ADD VARIABLE"** for each:
   - `DB_NAME` = `testbank_db`
   - `DB_USER` = `django_user`
   - `DB_HOST` = `/cloudsql/PROJECT_ID:REGION:exam-stellar-db` (use your connection name from Step 3)
   - `DB_PORT` = `5432`
   - `DEBUG` = `False`
   - `ALLOWED_HOSTS` = Leave empty for now (we'll update after first deployment)
   - `GS_BUCKET_NAME` = `exam-stellar-media`
   - `USE_CLOUD_STORAGE` = `True`

3. **Secrets** - Click **"ADD SECRET"** for each:
   - **Reference type**: `Secret Manager`
   - **Secret**: `django-secret-key`
   - **Version**: `latest`
   - **Variable name**: `SECRET_KEY`
   - Click **"ADD SECRET"** again:
     - **Secret**: `db-password`
     - **Version**: `latest`
     - **Variable name**: `DB_PASSWORD`

### Security Tab

1. Click **"SECURITY"** tab
2. **Service account**: 
   - Select **"Use a service account"**
   - Choose: `Compute Engine default service account` (or create custom one)
3. **Require authentication**: Leave **unchecked** (for public access)
4. **Allow unauthenticated invocations**: ✅ **Checked**

### Review and Deploy

1. Click **"CREATE"**
2. Wait 2-5 minutes for deployment
3. Once deployed, you'll see a green checkmark ✅
4. **Copy the service URL** (format: `https://exam-stellar-xxxxx-uc.a.run.app`)

---

## Step 9: Update ALLOWED_HOSTS

1. Go back to your Cloud Run service
2. Click on **"exam-stellar"** service name
3. Click **"EDIT & DEPLOY NEW REVISION"**
4. Go to **"VARIABLES & SECRETS"** tab
5. Find `ALLOWED_HOSTS` variable
6. Click the **pencil icon** to edit
7. Set value to your service URL (e.g., `exam-stellar-xxxxx-uc.a.run.app`)
8. Click **"DEPLOY"**

---

## Step 10: Run Database Migrations

### Option A: Using Cloud Run Jobs (Recommended)

1. Click **☰ (hamburger menu)** → **"Cloud Run"** → **"Jobs"**
2. Click **"CREATE JOB"**
3. Fill in:
   - **Job name**: `migrate-job`
   - **Region**: Same as your service (e.g., `us-central1`)
   - Click **"NEXT"**

4. **Container configuration**:
   - **Container image URL**: Same as your service image
   - **Command**: `python`
   - **Arguments**: `manage.py,migrate,--noinput`

5. **Connections** tab:
   - Add Cloud SQL connection: `exam-stellar-db`

6. **Variables & Secrets** tab:
   - Add same environment variables and secrets as your service:
     - `DB_NAME` = `testbank_db`
     - `DB_USER` = `django_user`
     - `DB_HOST` = `/cloudsql/PROJECT_ID:REGION:exam-stellar-db`
     - `DB_PORT` = `5432`
     - `SECRET_KEY` (from secret)
     - `DB_PASSWORD` (from secret)

7. Click **"CREATE"**

8. Once created, click **"EXECUTE JOB"**
9. Click **"EXECUTE"**
10. Wait for completion (check logs)

### Option B: Using Cloud Shell

1. Click the **Cloud Shell icon** (terminal icon) at the top right
2. Run:
```bash
gcloud run jobs execute migrate-job --region us-central1
```

---

## Step 11: Create Superuser (Admin User)

### Option A: Using Cloud Run Job

1. Go to **"Cloud Run"** → **"Jobs"**
2. Click **"CREATE JOB"**
3. Name: `createsuperuser-job`
4. Container image: Same as service
5. Command: `python`
6. Arguments: `manage.py,createsuperuser`
7. Add same connections, variables, and secrets
8. Click **"CREATE"** and **"EXECUTE JOB"**

**Note**: This will be interactive. For non-interactive, use Django shell or set environment variables.

### Option B: Via Django Admin (After Deployment)

1. Visit your Cloud Run service URL: `https://exam-stellar-xxxxx-uc.a.run.app/admin/`
2. If no superuser exists, Django will show an error
3. Use Cloud Shell to create superuser:
   ```bash
   gcloud run services update exam-stellar \
       --region us-central1 \
       --update-env-vars="CREATE_SUPERUSER=true"
   ```

---

## Step 12: Verify Deployment

1. **Check Service Status**:
   - Go to **"Cloud Run"** → Click on **"exam-stellar"**
   - Verify status shows **green checkmark** ✅
   - Check **"Metrics"** tab for requests

2. **Test Application**:
   - Click on the service URL
   - Verify homepage loads
   - Test admin panel: `https://your-service-url.run.app/admin/`

3. **Check Logs**:
   - In Cloud Run service page, go to **"LOGS"** tab
   - Verify no errors
   - Check for successful startup messages

4. **Test Database Connection**:
   - Try accessing admin panel
   - Create a test user account
   - Verify data persists

---

## Step 13: Configure Custom Domain (Optional)

1. Go to **"Cloud Run"** → **"exam-stellar"** service
2. Click **"MANAGE CUSTOM DOMAINS"** tab
3. Click **"ADD MAPPING"**
4. Enter your domain: `yourdomain.com`
5. Click **"CONTINUE"**
6. Follow DNS verification instructions:
   - Add TXT record to your domain DNS
   - Wait for verification (can take up to 24 hours)
7. Once verified, SSL certificate is automatically provisioned

---

## Step 14: Update and Redeploy (Future Changes)

### When You Make Code Changes:

1. **Push code to repository** (if using Cloud Build trigger, it auto-builds)

2. **Or manually rebuild**:
   - Go to **"Cloud Build"** → **"History"**
   - Click **"RUN"** → **"Run trigger"** or upload files

3. **Deploy new revision**:
   - Go to **"Cloud Run"** → **"exam-stellar"**
   - Click **"EDIT & DEPLOY NEW REVISION"**
   - Update container image to new version (if changed)
   - Or just click **"DEPLOY"** to use latest image

4. **Verify deployment**:
   - Check logs
   - Test application

---

## Step 15: Monitor and Manage

### View Logs

1. Go to **"Cloud Run"** → **"exam-stellar"**
2. Click **"LOGS"** tab
3. Filter by severity, time range, etc.

### View Metrics

1. Go to **"Cloud Run"** → **"exam-stellar"**
2. Click **"METRICS"** tab
3. View:
   - Request count
   - Latency
   - Error rate
   - Instance count

### Scale Service

1. Go to **"Cloud Run"** → **"exam-stellar"**
2. Click **"EDIT & DEPLOY NEW REVISION"**
3. Under **"Container"**:
   - Adjust **"Minimum instances"** (0 for cost savings)
   - Adjust **"Maximum instances"** (based on traffic)
4. Click **"DEPLOY"**

### Update Environment Variables

1. Go to **"Cloud Run"** → **"exam-stellar"**
2. Click **"EDIT & DEPLOY NEW REVISION"**
3. Go to **"VARIABLES & SECRETS"** tab
4. Add/edit/remove variables
5. Click **"DEPLOY"**

---

## Troubleshooting

### Service Won't Start

1. Check **"LOGS"** tab for errors
2. Verify environment variables are correct
3. Check Cloud SQL connection name format
4. Verify secrets are accessible

### Database Connection Errors

1. Verify Cloud SQL instance is running
2. Check connection name format: `PROJECT_ID:REGION:INSTANCE_NAME`
3. Verify Cloud SQL connection is added in Cloud Run service
4. Check database user credentials in secrets

### Static Files Not Loading

1. Verify `collectstatic` runs in docker-entrypoint.sh
2. Check `STATIC_ROOT` setting
3. Verify Cloud Storage bucket permissions (if using)

### 502 Bad Gateway

1. Check service logs
2. Verify container is listening on port 8080
3. Check health check endpoint
4. Increase timeout if needed

### High Costs

1. Set **"Minimum instances"** to `0`
2. Reduce **"Maximum instances"**
3. Use smaller machine types
4. Enable Cloud CDN for static files

---

## Quick Reference: Important URLs

- **Cloud Console**: https://console.cloud.google.com/
- **Cloud Run**: https://console.cloud.google.com/run
- **Cloud SQL**: https://console.cloud.google.com/sql
- **Cloud Storage**: https://console.cloud.google.com/storage
- **Secret Manager**: https://console.cloud.google.com/security/secret-manager
- **Cloud Build**: https://console.cloud.google.com/cloud-build
- **Artifact Registry**: https://console.cloud.google.com/artifacts

---

## Cost Optimization Tips

1. **Set minimum instances to 0** - Only pay when handling requests
2. **Use appropriate instance sizes** - Start with 2 CPU, 2GB RAM
3. **Enable Cloud CDN** - Cache static files
4. **Use Cloud Storage lifecycle policies** - Auto-delete old files
5. **Monitor usage** - Set up billing alerts

---

## Next Steps

1. ✅ Set up monitoring and alerts
2. ✅ Configure backup strategy for Cloud SQL
3. ✅ Set up staging environment
4. ✅ Implement CI/CD pipeline
5. ✅ Configure CDN for better performance
6. ✅ Set up error tracking (Sentry, etc.)

---

## Support

- **Google Cloud Documentation**: https://cloud.google.com/docs
- **Cloud Run Documentation**: https://cloud.google.com/run/docs
- **Cloud SQL Documentation**: https://cloud.google.com/sql/docs
- **Support**: https://cloud.google.com/support


