#!/usr/bin/env bash
# Deploy uncharged PageReady API to Cloud Run (plucky-agent).
# Payments stay off (PAGE_READY_ACCEPT_PAID=0).
set -euo pipefail

PROJECT="${GCP_PROJECT:-plucky-agent-313422}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-page-ready-api}"
IMAGE="gcr.io/${PROJECT}/${SERVICE}:$(git rev-parse --short HEAD)"

echo "Project=$PROJECT Region=$REGION Service=$SERVICE"
gcloud config set project "$PROJECT"
gcloud builds submit --tag "$IMAGE" .
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 120 \
  --concurrency 5 \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars "PAGE_READY_ACCEPT_PAID=0,PAGE_READY_RATE_PER_MIN=10" \
  --quiet

gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)'
