# Deploy uncharged PageReady API to Cloud Run (plucky-agent).
# Payments stay off (PAGE_READY_ACCEPT_PAID=0).
$ErrorActionPreference = "Stop"

$Project = if ($env:GCP_PROJECT) { $env:GCP_PROJECT } else { "plucky-agent-313422" }
$Region = if ($env:REGION) { $env:REGION } else { "us-central1" }
$Service = if ($env:SERVICE) { $env:SERVICE } else { "page-ready-api" }
$sha = (git rev-parse --short HEAD).Trim()
$Image = "gcr.io/${Project}/${Service}:${sha}"

Write-Host "Project=$Project Region=$Region Service=$Service Image=$Image"
gcloud config set project $Project | Out-Null
gcloud builds submit --tag $Image .
gcloud run deploy $Service `
  --image $Image `
  --region $Region `
  --platform managed `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 1 `
  --timeout 120 `
  --concurrency 5 `
  --min-instances 0 `
  --max-instances 3 `
  --set-env-vars "PAGE_READY_ACCEPT_PAID=0,PAGE_READY_RATE_PER_MIN=10" `
  --quiet

gcloud run services describe $Service --region $Region --format="value(status.url)"
