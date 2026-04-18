#!/usr/bin/env bash
# Deploy the chatbot to Google Cloud Run.
#
# Prerequisites (one-time setup):
#   1. gcloud CLI authenticated: `gcloud auth login`
#   2. PROJECT_ID env var set: `export PROJECT_ID=my-gcp-project`
#   3. Required APIs enabled:
#        gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
#          secretmanager.googleapis.com redis.googleapis.com vpcaccess.googleapis.com
#   4. Memorystore Redis instance created (or remove the VPC config)
#   5. Anthropic API key stored in Secret Manager:
#        echo -n "$ANTHROPIC_API_KEY" | gcloud secrets create anthropic-api-key --data-file=-

set -euo pipefail

PROJECT_ID="${PROJECT_ID:?PROJECT_ID is required}"
REGION="${REGION:-europe-west1}"
SERVICE_NAME="${SERVICE_NAME:-rag-metering}"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "▶ Building image ${IMAGE}…"
gcloud builds submit --tag "${IMAGE}" --project "${PROJECT_ID}"

echo "▶ Deploying to Cloud Run (${REGION})…"
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --platform managed \
  --memory 2Gi \
  --cpu 2 \
  --concurrency 20 \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 60 \
  --cpu-boost \
  --set-env-vars "LLM_MODEL=claude-sonnet-4-5,LOG_LEVEL=INFO" \
  --set-secrets "ANTHROPIC_API_KEY=anthropic-api-key:latest" \
  --allow-unauthenticated

echo "✅ Deployed. Service URL:"
gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" \
  --format='value(status.url)'
