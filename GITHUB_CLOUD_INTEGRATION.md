# GitHub to Google Cloud Integration Guide

Complete step-by-step guide to connect your GitHub repository to Google Cloud for automated builds and deployments.

---

## Overview

This guide will help you:
1. Connect GitHub repository to Google Cloud
2. Set up Cloud Build triggers for automatic builds
3. Automatically deploy to Cloud Run when code is pushed
4. Set up CI/CD pipeline

---

## Step 1: Connect GitHub Repository to Google Cloud

### Option A: Via Cloud Source Repositories (Recommended)

1. **Go to Cloud Source Repositories**
   - Open [Google Cloud Console](https://console.cloud.google.com/)
   - Click **☰ (hamburger menu)** → **"Source Repositories"**

2. **Add Repository**
   - Click **"ADD REPOSITORY"**
   - Select **"Connect external repository"**
   - Choose **"GitHub (Cloud Source Repositories)"**

3. **Authenticate GitHub**
   - Click **"CONNECT GITHUB"**
   - You'll be redirected to GitHub
   - Sign in to GitHub (if not already)
   - Authorize Google Cloud Build to access your repositories
   - Select repositories you want to connect:
     - Choose **"Only select repositories"**
     - Select your repository: `malhajri07/Test_Bank` (or your repo name)
   - Click **"Install"** or **"Authorize"**

4. **Select Repository**
   - Back in Google Cloud Console
   - Select your GitHub account
   - Select your repository: `Test_Bank`
   - Click **"CONNECT"**

5. **Verify Connection**
   - You should see your repository listed in Cloud Source Repositories
   - Repository URL format: `https://source.developers.google.com/p/PROJECT_ID/r/REPO_NAME`

---

## Step 2: Set Up Cloud Build Trigger

### Create Build Trigger

1. **Go to Cloud Build**
   - Click **☰ (hamburger menu)** → **"Cloud Build"** → **"Triggers"**
   - Click **"CREATE TRIGGER"**

2. **Configure Trigger**
   - **Name**: `exam-stellar-github-trigger`
   - **Description**: `Auto-build on push to main branch`

3. **Event Configuration**
   - **Event**: Select **"Push to a branch"**
   - **Source**: Select your connected GitHub repository
   - **Branch**: `^main$` (or your main branch name)
   - **Configuration**: Select **"Cloud Build configuration file (yaml or json)"**
   - **Location**: `cloudbuild.yaml`

4. **Advanced Options** (Optional)
   - **Substitution variables**: Leave default
   - **Service account**: Use default Cloud Build service account
   - **Timeout**: `1200s` (20 minutes)

5. **Create Trigger**
   - Click **"CREATE"**
   - Trigger is now active!

---

## Step 3: Verify cloudbuild.yaml File

Make sure `cloudbuild.yaml` exists in your repository root with this content:

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
  
  # Push latest tag
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:latest']

images:
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:$SHORT_SHA'
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:latest'

options:
  machineType: 'E2_HIGHCPU_8'
  logging: CLOUD_LOGGING_ONLY

timeout: '1200s'
```

**Important**: Replace `us-central1` with your actual region if different.

---

## Step 4: Test the Integration

1. **Make a Small Change**
   ```bash
   # In your local repository
   echo "# Test build" >> README.md
   git add README.md
   git commit -m "Test Cloud Build trigger"
   git push origin main
   ```

2. **Monitor Build**
   - Go to **"Cloud Build"** → **"History"**
   - You should see a new build starting automatically
   - Click on the build to see logs in real-time
   - Wait for build to complete (5-10 minutes)

3. **Verify Image**
   - Go to **"Artifact Registry"** → **"exam-stellar-repo"**
   - You should see new images tagged with commit SHA and `latest`

---

## Step 5: Set Up Automatic Deployment to Cloud Run

### Option A: Add Deployment Step to cloudbuild.yaml

Update your `cloudbuild.yaml` to automatically deploy after build:

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
  
  # Push latest tag
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:latest']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'exam-stellar'
      - '--image'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:$SHORT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'

images:
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:$SHORT_SHA'
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:latest'

options:
  machineType: 'E2_HIGHCPU_8'
  logging: CLOUD_LOGGING_ONLY

timeout: '1200s'
```

### Grant Cloud Build Permissions

1. **Get Cloud Build Service Account**
   - Go to **"IAM & Admin"** → **"Service Accounts"**
   - Find: `PROJECT_NUMBER@cloudbuild.gserviceaccount.com`
   - Note the PROJECT_NUMBER

2. **Grant Cloud Run Admin Role**
   - Click on the service account
   - Go to **"PERMISSIONS"** tab
   - Click **"GRANT ACCESS"**
   - **New principals**: `PROJECT_NUMBER@cloudbuild.gserviceaccount.com`
   - **Role**: `Cloud Run Admin`
   - Click **"SAVE"**

3. **Grant Artifact Registry Writer Role**
   - Same service account
   - Add role: `Artifact Registry Writer`

---

## Step 6: Set Up Separate Triggers for Different Branches

### Create Staging Trigger

1. **Create New Trigger**
   - Name: `exam-stellar-staging-trigger`
   - Event: `Push to a branch`
   - Branch: `^staging$`
   - Configuration: `cloudbuild.staging.yaml` (create this file)

2. **Create Staging Build File** (`cloudbuild.staging.yaml`)
   ```yaml
   steps:
     - name: 'gcr.io/cloud-builders/docker'
       args: ['build', '-t', 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:staging-$SHORT_SHA', '.']
     - name: 'gcr.io/cloud-builders/docker'
       args: ['push', 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:staging-$SHORT_SHA']
     - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
       entrypoint: gcloud
       args:
         - 'run'
         - 'deploy'
         - 'exam-stellar-staging'
         - '--image'
         - 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:staging-$SHORT_SHA'
         - '--region'
         - 'us-central1'
   ```

### Create Production Trigger

1. **Create Production Trigger**
   - Name: `exam-stellar-production-trigger`
   - Event: `Push to a branch`
   - Branch: `^main$` or `^production$`
   - Configuration: `cloudbuild.yaml` (your main file)

---

## Step 7: Set Up Pull Request Builds (Optional)

1. **Create PR Trigger**
   - Name: `exam-stellar-pr-trigger`
   - Event: `Pull request`
   - Source: Your repository
   - Base branch: `main`
   - Configuration: `cloudbuild.yaml`

2. **PR Builds Will**
   - Build Docker image
   - Run tests (if configured)
   - Push to Artifact Registry with PR number tag
   - **NOT deploy** to Cloud Run (safety)

---

## Step 8: Configure Build Notifications

### Email Notifications

1. **Go to Cloud Build Settings**
   - **"Cloud Build"** → **"Settings"**
   - **"Notifications"** tab
   - Enable **"Email notifications"**
   - Add email addresses
   - Select events: Build success, Build failure

### Slack Notifications (Optional)

1. **Create Slack Webhook**
   - Go to Slack → Apps → Incoming Webhooks
   - Create webhook URL

2. **Add to cloudbuild.yaml**
   ```yaml
   steps:
     # ... your build steps ...
   
     # Notify Slack
     - name: 'curlimages/curl'
       args:
         - '--request'
         - 'POST'
         - '${_SLACK_WEBHOOK_URL}'
         - '--header'
         - 'Content-Type: application/json'
         - '--data'
         - '{"text":"Build completed: $BUILD_ID"}'
   ```

---

## Step 9: Add Build Status Badge to GitHub

1. **Get Badge URL**
   - Go to **"Cloud Build"** → **"Triggers"**
   - Click on your trigger
   - Copy the **"Status badge URL"**

2. **Add to README.md**
   ```markdown
   [![Build Status](https://storage.googleapis.com/cloud-build-badges/build-status-badge.svg)](https://console.cloud.google.com/cloud-build/triggers)
   ```

---

## Step 10: Workflow Summary

### Complete CI/CD Flow

```
Developer pushes to GitHub
    ↓
GitHub webhook triggers Cloud Build
    ↓
Cloud Build pulls code from GitHub
    ↓
Docker image built using cloudbuild.yaml
    ↓
Image pushed to Artifact Registry
    ↓
Cloud Run service updated with new image
    ↓
New revision deployed automatically
    ↓
Service URL updated (or new revision created)
```

### Typical Workflow

1. **Development**
   ```bash
   git checkout -b feature/new-feature
   # Make changes
   git commit -m "Add new feature"
   git push origin feature/new-feature
   ```

2. **Create Pull Request**
   - PR triggers build (tests only, no deploy)
   - Review code
   - Merge to `main`

3. **Automatic Deployment**
   - Merge to `main` triggers production build
   - Build completes → Image pushed → Cloud Run updated
   - New version live in ~10-15 minutes

---

## Troubleshooting

### Build Fails

1. **Check Build Logs**
   - Go to **"Cloud Build"** → **"History"**
   - Click on failed build
   - Review error messages

2. **Common Issues**
   - **Permission denied**: Grant Cloud Build service account proper roles
   - **Docker build fails**: Check Dockerfile syntax
   - **Push fails**: Verify Artifact Registry permissions
   - **Deploy fails**: Check Cloud Run service exists

### Trigger Not Firing

1. **Verify Repository Connection**
   - Go to **"Source Repositories"**
   - Check repository is connected
   - Test by clicking **"MANUAL SYNC"**

2. **Check Trigger Configuration**
   - Verify branch name matches (case-sensitive)
   - Check `cloudbuild.yaml` exists in root
   - Verify file path is correct

3. **Check GitHub Webhook**
   - Go to GitHub repository → **"Settings"** → **"Webhooks"**
   - Verify Google Cloud webhook exists
   - Check recent deliveries for errors

### Deployment Not Updating

1. **Check Cloud Run Service**
   - Verify service name matches in cloudbuild.yaml
   - Check region matches
   - Verify service account has permissions

2. **Check Image Tags**
   - Verify image exists in Artifact Registry
   - Check image tag matches deployment command

---

## Advanced Configuration

### Build with Tests

Update `cloudbuild.yaml` to run tests:

```yaml
steps:
  # Install dependencies and run tests
  - name: 'python:3.9'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install -r requirements.txt
        python manage.py test
    dir: '.'

  # Build Docker image (only if tests pass)
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:$SHORT_SHA', '.']
  
  # ... rest of steps
```

### Conditional Deployment

Only deploy on main branch:

```yaml
steps:
  # ... build steps ...
  
  # Deploy only if branch is main
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        if [ "$BRANCH_NAME" = "main" ]; then
          gcloud run deploy exam-stellar --image us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:$SHORT_SHA --region us-central1
        fi
```

### Run Migrations Before Deployment

```yaml
steps:
  # ... build and push steps ...
  
  # Run migrations
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'jobs'
      - 'execute'
      - 'migrate-job'
      - '--region'
      - 'us-central1'
  
  # Deploy new revision
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'exam-stellar'
      - '--image'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/exam-stellar-repo/exam-stellar:$SHORT_SHA'
      - '--region'
      - 'us-central1'
```

---

## Security Best Practices

1. **Use Secret Manager**
   - Store sensitive data in Secret Manager
   - Reference secrets in Cloud Run, not in code

2. **Limit Permissions**
   - Use least privilege principle
   - Only grant necessary roles to service accounts

3. **Scan Images**
   - Enable Container Analysis API
   - Scan for vulnerabilities automatically

4. **Review Build Logs**
   - Regularly review build logs
   - Set up alerts for failures

---

## Cost Optimization

1. **Use Build Timeouts**
   - Set appropriate timeout in cloudbuild.yaml
   - Avoid infinite builds

2. **Use Appropriate Machine Types**
   - `E2_HIGHCPU_8` for faster builds
   - `E2_MEDIUM` for smaller projects

3. **Clean Up Old Images**
   - Set lifecycle policies in Artifact Registry
   - Delete images older than 30 days

---

## Quick Reference

### Manual Build Trigger

```bash
# Trigger build manually via gcloud
gcloud builds triggers run exam-stellar-github-trigger --branch main
```

### View Build Status

- Web: **Cloud Build** → **History**
- CLI: `gcloud builds list`

### View Trigger Status

- Web: **Cloud Build** → **Triggers**
- CLI: `gcloud builds triggers list`

---

## Next Steps

1. ✅ Test the integration with a small change
2. ✅ Set up staging environment
3. ✅ Configure notifications
4. ✅ Add build status badge to README
5. ✅ Set up automated testing
6. ✅ Configure rollback strategy

---

## Support Resources

- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [GitHub Integration Guide](https://cloud.google.com/build/docs/automating-builds/create-github-app-triggers)
- [Cloud Run Deployment](https://cloud.google.com/run/docs/deploying)

