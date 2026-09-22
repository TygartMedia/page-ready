# Deploy the PageReady API to Cloud Run.
# Requires GCP_PROJECT. Payments stay off (PAGE_READY_ACCEPT_PAID=0).
$ErrorActionPreference = "Continue"

if (-not $env:GCP_PROJECT) { throw "Set GCP_PROJECT to your Google Cloud project id" }
$Project = $env:GCP_PROJECT
$Region = if ($env:REGION) { $env:REGION } else { "us-central1" }
$Service = if ($env:SERVICE) { $env:SERVICE } else { "page-ready-api" }
$sha = (git rev-parse --short HEAD).Trim()
$Image = "gcr.io/${Project}/${Service}:${sha}"

Write-Host "Project=$Project Region=$Region Service=$Service Image=$Image"
cmd /c "gcloud config set project $Project"
if ($LASTEXITCODE -ne 0) { throw "gcloud config set project failed" }

cmd /c "gcloud builds submit --tag $Image ."
if ($LASTEXITCODE -ne 0) { throw "gcloud builds submit failed" }

cmd /c "gcloud run deploy $Service --image $Image --region $Region --platform managed --allow-unauthenticated --memory 2Gi --cpu 1 --timeout 120 --concurrency 5 --min-instances 0 --max-instances 3 --set-env-vars PAGE_READY_ACCEPT_PAID=0,PAGE_READY_RATE_PER_MIN=10 --quiet"
if ($LASTEXITCODE -ne 0) { throw "gcloud run deploy failed" }

cmd /c "gcloud run services describe $Service --region $Region --format=value(status.url)"
