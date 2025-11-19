#!/bin/bash
# Deployment script for Google Cloud Run
# Usage: ./deploy-cloudrun.sh [project-id] [region]

set -e

# Configuration
PROJECT_ID=${1:-${GOOGLE_CLOUD_PROJECT:-"your-project-id"}}
REGION=${2:-"us-central1"}
SERVICE_NAME="exam-stellar"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
DB_INSTANCE_NAME="exam-stellar-db"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deploying Exam Stellar to Google Cloud Run${NC}"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo -e "${YELLOW}Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    storage-component.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    --quiet

# Build and push Docker image
echo -e "${YELLOW}Building and pushing Docker image...${NC}"
gcloud builds submit --tag $IMAGE_NAME:latest --quiet

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="DB_HOST=/cloudsql/$PROJECT_ID:$REGION:$DB_INSTANCE_NAME,DEBUG=False" \
    --add-cloudsql-instances=$PROJECT_ID:$REGION:$DB_INSTANCE_NAME \
    --set-secrets="SECRET_KEY=django-secret-key:latest,DB_PASSWORD=db-password:latest,STRIPE_SECRET_KEY=stripe-secret-key:latest" \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --min-instances=1 \
    --port=8080 \
    --quiet

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")

echo ""
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "Service URL: ${GREEN}$SERVICE_URL${NC}"
echo ""
echo "Next steps:"
echo "1. Run migrations: gcloud run jobs create migrate --image $IMAGE_NAME:latest --region $REGION --command python --args 'manage.py,migrate'"
echo "2. Create superuser: gcloud run jobs create createsuperuser --image $IMAGE_NAME:latest --region $REGION --command python --args 'manage.py,createsuperuser'"
echo "3. Collect static files: gcloud run jobs create collectstatic --image $IMAGE_NAME:latest --region $REGION --command python --args 'manage.py,collectstatic,--noinput'"

