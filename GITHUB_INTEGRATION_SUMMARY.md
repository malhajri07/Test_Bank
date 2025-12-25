# GitHub to Google Cloud Integration - Quick Summary

## The Plan: Connect GitHub → Google Cloud → Auto Deploy

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   GitHub    │  Push   │ Google Cloud │  Build  │ Cloud Run   │
│  Repository │ ──────> │    Build     │ ──────> │   Service   │
└─────────────┘         └──────────────┘         └─────────────┘
```

---

## 5 Simple Steps

### ✅ Step 1: Connect GitHub Repository
**Location**: Cloud Console → Source Repositories → ADD REPOSITORY
- Click "Connect external repository"
- Choose "GitHub"
- Authorize Google Cloud
- Select your repository
- Click "CONNECT"

**Result**: GitHub repo now visible in Google Cloud

---

### ✅ Step 2: Create Build Trigger
**Location**: Cloud Console → Cloud Build → Triggers → CREATE TRIGGER
- Name: `exam-stellar-github-trigger`
- Event: `Push to a branch`
- Source: Your GitHub repository
- Branch: `^main$`
- Configuration: `cloudbuild.yaml`

**Result**: Automatic builds when code is pushed

---

### ✅ Step 3: Verify cloudbuild.yaml
**File**: `cloudbuild.yaml` in repository root
- Contains Docker build steps
- Pushes to Artifact Registry
- (Optional) Deploys to Cloud Run

**Result**: Build configuration ready

---

### ✅ Step 4: Grant Permissions
**Location**: IAM & Admin → Service Accounts
- Find: `PROJECT_NUMBER@cloudbuild.gserviceaccount.com`
- Grant roles:
  - `Cloud Run Admin`
  - `Artifact Registry Writer`

**Result**: Cloud Build can deploy

---

### ✅ Step 5: Test It!
```bash
# Make a small change
echo "Test" >> README.md
git add README.md
git commit -m "Test Cloud Build"
git push origin main
```

**Result**: Build starts automatically! 🎉

---

## What Happens Automatically

1. **You push code** → GitHub receives changes
2. **GitHub webhook** → Notifies Google Cloud Build
3. **Cloud Build triggers** → Starts build process
4. **Docker image built** → Using your Dockerfile
5. **Image pushed** → To Artifact Registry
6. **Cloud Run updated** → New version deployed (if configured)
7. **New revision live** → Your changes are live!

**Total time**: ~10-15 minutes

---

## Files You Need

### 1. `cloudbuild.yaml` (Already created ✅)
```yaml
steps:
  - Build Docker image
  - Push to Artifact Registry
  - (Optional) Deploy to Cloud Run
```

### 2. `Dockerfile` (Already exists ✅)
- Multi-stage build
- Optimized for Cloud Run
- Includes all dependencies

### 3. `.dockerignore` (Already exists ✅)
- Excludes unnecessary files
- Reduces build time

---

## Two Integration Options

### Option A: Build Only (Recommended for First Time)
- Builds Docker image
- Pushes to Artifact Registry
- **Manual deployment** via Cloud Run console

**Use when**: You want to review before deploying

### Option B: Build + Deploy (Full CI/CD)
- Builds Docker image
- Pushes to Artifact Registry
- **Automatically deploys** to Cloud Run

**Use when**: You trust your tests and want full automation

---

## Enable Automatic Deployment

Uncomment the deployment step in `cloudbuild.yaml`:

```yaml
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
```

---

## Branch Strategy

### Main Branch → Production
- Trigger: `^main$`
- Deploys to: `exam-stellar` (production)
- Auto-deploy: ✅ Enabled

### Staging Branch → Staging
- Trigger: `^staging$`
- Deploys to: `exam-stellar-staging`
- Auto-deploy: ✅ Enabled

### Feature Branches → Build Only
- Trigger: `^feature/.*`
- Deploys to: Nothing (build only)
- Use for: Testing builds

---

## Monitoring

### View Builds
- **Web**: Cloud Build → History
- **CLI**: `gcloud builds list`

### View Logs
- Click on any build in History
- See real-time logs
- Download logs if needed

### Build Status Badge
Add to your README.md:
```markdown
[![Build Status](YOUR_BADGE_URL)](YOUR_TRIGGER_URL)
```

---

## Troubleshooting

### ❌ Build Not Triggering?
1. Check GitHub webhook is active
2. Verify branch name matches (case-sensitive)
3. Ensure `cloudbuild.yaml` exists in root

### ❌ Build Failing?
1. Check build logs
2. Verify Dockerfile syntax
3. Check permissions

### ❌ Deployment Failing?
1. Verify Cloud Run service exists
2. Check service account permissions
3. Verify image exists in Artifact Registry

---

## Security Checklist

- [ ] Secrets stored in Secret Manager (not in code)
- [ ] Service account has minimal permissions
- [ ] Build logs don't expose sensitive data
- [ ] GitHub webhook is secure
- [ ] Only trusted branches trigger deployment

---

## Cost Considerations

- **Cloud Build**: First 120 build-minutes/day free
- **Artifact Registry**: First 0.5 GB free
- **Cloud Run**: Pay per request (generous free tier)

**Estimated cost**: ~$0-5/month for small projects

---

## Next Steps After Integration

1. ✅ Test with a small change
2. ✅ Set up staging environment
3. ✅ Configure email notifications
4. ✅ Add build status badge
5. ✅ Set up automated tests
6. ✅ Configure rollback strategy

---

## Quick Commands

```bash
# Trigger build manually
gcloud builds triggers run exam-stellar-github-trigger --branch main

# List builds
gcloud builds list

# View build logs
gcloud builds log BUILD_ID

# List triggers
gcloud builds triggers list
```

---

## Support

- **Full Guide**: See `GITHUB_CLOUD_INTEGRATION.md`
- **Deployment Guide**: See `DEPLOYMENT_WEB_CONSOLE.md`
- **Cloud Build Docs**: https://cloud.google.com/build/docs

---

**Status**: ⬜ Not Started | ⬜ In Progress | ⬜ Completed

**Last Updated**: _______________

