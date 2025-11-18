#!/bin/bash
# Initial GCP setup script
# Creates Cloud SQL, Storage buckets, and secrets

set -e

# Configuration
PROJECT_ID=${1:-${GOOGLE_CLOUD_PROJECT:-"your-project-id"}}
REGION=${2:-"us-central1"}
DB_INSTANCE_NAME="exam-stellar-db"
DB_NAME="testbank_db"
DB_USER="django_user"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Setting up GCP infrastructure for Exam Stellar${NC}"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Enable APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    storage-component.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    --quiet

# Create Cloud SQL instance
echo -e "${YELLOW}Creating Cloud SQL instance...${NC}"
read -sp "Enter database root password: " DB_ROOT_PASSWORD
echo ""

gcloud sql instances create $DB_INSTANCE_NAME \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --root-password=$DB_ROOT_PASSWORD \
    --storage-type=SSD \
    --storage-size=20GB \
    --backup-start-time=03:00 \
    --enable-bin-log \
    --quiet

# Create database
echo -e "${YELLOW}Creating database...${NC}"
gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE_NAME --quiet

# Create database user
read -sp "Enter database user password: " DB_USER_PASSWORD
echo ""

gcloud sql users create $DB_USER \
    --instance=$DB_INSTANCE_NAME \
    --password=$DB_USER_PASSWORD \
    --quiet

# Store database password in Secret Manager
echo -n "$DB_USER_PASSWORD" | gcloud secrets create db-password \
    --data-file=- \
    --replication-policy="automatic" \
    --quiet || echo "Secret db-password already exists"

# Create Cloud Storage buckets
echo -e "${YELLOW}Creating Cloud Storage buckets...${NC}"
gsutil mb -p $PROJECT_ID -l $REGION gs://$PROJECT_ID-exam-stellar-media || echo "Bucket already exists"
gsutil mb -p $PROJECT_ID -l $REGION gs://$PROJECT_ID-exam-stellar-static || echo "Bucket already exists"

# Set bucket permissions
gsutil iam ch allUsers:objectViewer gs://$PROJECT_ID-exam-stellar-media
gsutil iam ch allUsers:objectViewer gs://$PROJECT_ID-exam-stellar-static

# Create secrets
echo -e "${YELLOW}Creating secrets...${NC}"
read -sp "Enter Django SECRET_KEY: " SECRET_KEY
echo ""
echo -n "$SECRET_KEY" | gcloud secrets create django-secret-key \
    --data-file=- \
    --replication-policy="automatic" \
    --quiet || echo "Secret django-secret-key already exists"

read -sp "Enter Stripe Secret Key (optional, press Enter to skip): " STRIPE_SECRET
if [ ! -z "$STRIPE_SECRET" ]; then
    echo -n "$STRIPE_SECRET" | gcloud secrets create stripe-secret-key \
        --data-file=- \
        --replication-policy="automatic" \
        --quiet || echo "Secret stripe-secret-key already exists"
fi

# Grant Cloud Run service account access to secrets
echo -e "${YELLOW}Configuring IAM permissions...${NC}"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding django-secret-key \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

gcloud secrets add-iam-policy-binding db-password \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Created resources:"
echo "- Cloud SQL instance: $DB_INSTANCE_NAME"
echo "- Database: $DB_NAME"
echo "- Database user: $DB_USER"
echo "- Storage buckets: $PROJECT_ID-exam-stellar-media, $PROJECT_ID-exam-stellar-static"
echo "- Secrets: django-secret-key, db-password"
echo ""
echo "Next: Run ./deploy-cloudrun.sh $PROJECT_ID $REGION"

