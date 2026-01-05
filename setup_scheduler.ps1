# PowerShell script to setup Cloud Scheduler
# Triggers the agent every Monday at 7 AM

$ErrorActionPreference = "Stop"  # Exit on error

# Configuration
$PROJECT_ID = "avisia-training"
$REGION = "europe-west1"
$SCHEDULER_JOB_NAME = "ga4-weekly-analysis"
$SERVICE_NAME = "ga4-analytics-agent"
$TIMEZONE = "Europe/Paris"  # Adjust to your timezone

Write-Host "⏰ Setting up Cloud Scheduler for GA4 Analytics Agent" -ForegroundColor Green
Write-Host "Project: $PROJECT_ID"
Write-Host "Schedule: Every Monday at 7:00 AM $TIMEZONE"
Write-Host ""

# 1. Set the GCP project
Write-Host "📋 Step 1: Setting GCP project..." -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

# 2. Get the Cloud Run service URL
Write-Host ""
Write-Host "📍 Step 2: Getting Cloud Run service URL..." -ForegroundColor Cyan
$SERVICE_URL = gcloud run services describe $SERVICE_NAME `
    --platform managed `
    --region $REGION `
    --format 'value(status.url)' 2>$null

if ([string]::IsNullOrEmpty($SERVICE_URL)) {
    Write-Host "❌ Error: Could not find Cloud Run service $SERVICE_NAME" -ForegroundColor Red
    Write-Host "Please deploy the agent first using .\deploy_agent.ps1" -ForegroundColor Red
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

$ENDPOINT = "$SERVICE_URL/run"
Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Green
Write-Host "Endpoint: $ENDPOINT" -ForegroundColor Green

# 3. Create service account for Cloud Scheduler
Write-Host ""
Write-Host "🔑 Step 3: Creating service account for Cloud Scheduler..." -ForegroundColor Cyan
$SA_NAME = "ga4-scheduler"
$SA_EMAIL = "$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

try {
    gcloud iam service-accounts create $SA_NAME `
        --display-name "GA4 Analytics Scheduler" `
        --description "Service account for Cloud Scheduler to trigger GA4 analytics agent" 2>$null
    Write-Host "Service account created successfully"
} catch {
    Write-Host "Service account already exists (this is OK)" -ForegroundColor Yellow
}

# 4. Grant permissions to invoke Cloud Run
Write-Host ""
Write-Host "🔐 Step 4: Granting Cloud Run Invoker permissions..." -ForegroundColor Cyan
gcloud run services add-iam-policy-binding $SERVICE_NAME `
    --region=$REGION `
    --member="serviceAccount:$SA_EMAIL" `
    --role="roles/run.invoker"

# 5. Delete existing scheduler job if exists
Write-Host ""
Write-Host "🗑️  Step 5: Removing existing scheduler job if exists..." -ForegroundColor Cyan
try {
    gcloud scheduler jobs delete $SCHEDULER_JOB_NAME `
        --location=$REGION `
        --quiet 2>$null
    Write-Host "Existing job deleted"
} catch {
    Write-Host "No existing job to delete (this is OK)" -ForegroundColor Yellow
}

# 6. Create Cloud Scheduler job
Write-Host ""
Write-Host "📅 Step 6: Creating Cloud Scheduler job..." -ForegroundColor Cyan
gcloud scheduler jobs create http $SCHEDULER_JOB_NAME `
    --location=$REGION `
    --schedule="0 7 * * 1" `
    --time-zone="$TIMEZONE" `
    --uri="$ENDPOINT" `
    --http-method=POST `
    --oidc-service-account-email=$SA_EMAIL `
    --oidc-token-audience="$SERVICE_URL" `
    --headers="Content-Type=application/json" `
    --message-body='{"trigger":"scheduled","source":"cloud-scheduler"}'

# 7. Test the scheduler job (optional)
Write-Host ""
Write-Host "🧪 Step 7: Testing the scheduler job..." -ForegroundColor Cyan
$response = Read-Host "Do you want to trigger a test run now? (y/N)"
if ($response -eq "y" -or $response -eq "Y") {
    Write-Host "Triggering test run..." -ForegroundColor Cyan
    gcloud scheduler jobs run $SCHEDULER_JOB_NAME --location=$REGION
    Write-Host "Test run triggered! Check Cloud Run logs for results." -ForegroundColor Green
    Write-Host ""
    Write-Host "To view logs, run:"
    Write-Host "gcloud logging read 'resource.labels.service_name=$SERVICE_NAME' --limit 50"
}

Write-Host ""
Write-Host "✅ Cloud Scheduler setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Schedule: Every Monday at 7:00 AM $TIMEZONE"
Write-Host "  Job Name: $SCHEDULER_JOB_NAME"
Write-Host "  Endpoint: $ENDPOINT"
Write-Host "  Service Account: $SA_EMAIL"
Write-Host ""
Write-Host "Recipients:" -ForegroundColor Cyan
Write-Host "  - mjacobson@avisia.fr"
Write-Host "  - mnunez@avisia.fr"
Write-Host "  - adejullien@avisia.fr"
Write-Host ""
Write-Host "Commands to manage the scheduler:" -ForegroundColor Cyan
Write-Host "  View job:"
Write-Host "    gcloud scheduler jobs describe $SCHEDULER_JOB_NAME --location=$REGION"
Write-Host ""
Write-Host "  Trigger manually:"
Write-Host "    gcloud scheduler jobs run $SCHEDULER_JOB_NAME --location=$REGION"
Write-Host ""
Write-Host "  Pause:"
Write-Host "    gcloud scheduler jobs pause $SCHEDULER_JOB_NAME --location=$REGION"
Write-Host ""
Write-Host "  Resume:"
Write-Host "    gcloud scheduler jobs resume $SCHEDULER_JOB_NAME --location=$REGION"
Write-Host ""
Write-Host "  View logs:"
Write-Host "    gcloud logging read 'resource.labels.service_name=$SERVICE_NAME' --limit 50"

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
