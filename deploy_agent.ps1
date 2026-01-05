# PowerShell script to deploy GA4 Analytics Agent to Cloud Run

$ErrorActionPreference = "Stop"  # Exit on error

# Configuration
$PROJECT_ID = "avisia-training"
$REGION = "europe-west1"
$SERVICE_NAME = "ga4-analytics-agent"
$REPOSITORY = "cloud-run-source-deploy"
$IMAGE_NAME = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$SERVICE_NAME"
$GA4_MCP_SERVER_URL = "https://ga4-http-api-1062626335546.europe-west1.run.app"


# Gmail OAuth2 credentials (set these as environment variables before running)
$GMAIL_OAUTH_CLIENT_ID = $env:GMAIL_OAUTH_CLIENT_ID
$GMAIL_OAUTH_CLIENT_SECRET = $env:GMAIL_OAUTH_CLIENT_SECRET
$GMAIL_OAUTH_REFRESH_TOKEN = $env:GMAIL_OAUTH_REFRESH_TOKEN

Write-Host " Deploying GA4 Analytics Agent to Cloud Run" -ForegroundColor Green
Write-Host "Project: $PROJECT_ID"
Write-Host "Region: $REGION"
Write-Host "Service: $SERVICE_NAME"
Write-Host ""

# Check if MCP server URL has been updated
if ($GA4_MCP_SERVER_URL -like "*XXXXXX*") {
    Write-Host "  WARNING: GA4_MCP_SERVER_URL contains placeholder 'XXXXXX'" -ForegroundColor Red
    Write-Host "Please update the GA4_MCP_SERVER_URL variable in this script with your actual MCP server URL" -ForegroundColor Red
    Write-Host ""
    $response = Read-Host "Do you want to continue anyway? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "Deployment cancelled." -ForegroundColor Yellow
        exit 1
    }
}

# Check if Gmail OAuth2 credentials are set
if (-not $GMAIL_OAUTH_CLIENT_ID -or -not $GMAIL_OAUTH_CLIENT_SECRET -or -not $GMAIL_OAUTH_REFRESH_TOKEN) {
    Write-Host "  WARNING: Gmail OAuth2 credentials not set!" -ForegroundColor Red
    Write-Host ""
    Write-Host "The following environment variables are required:" -ForegroundColor Yellow
    Write-Host "  - GMAIL_OAUTH_CLIENT_ID"
    Write-Host "  - GMAIL_OAUTH_CLIENT_SECRET"
    Write-Host "  - GMAIL_OAUTH_REFRESH_TOKEN"
    Write-Host ""
    Write-Host "To obtain these credentials:" -ForegroundColor Cyan
    Write-Host "1. Run: .\get_gmail_refresh_token.ps1 path\to\client_secret.json"
    Write-Host "2. Copy the environment variables from the output"
    Write-Host "3. Set them in your PowerShell session"
    Write-Host "4. Run this deployment script again"
    Write-Host ""
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit 1
}

# 1. Set the GCP project
Write-Host ""
Write-Host " Step 1: Setting GCP project..." -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

# 2. Enable required APIs
Write-Host ""
Write-Host " Step 2: Enabling required APIs..." -ForegroundColor Cyan
Write-Host "This may take a few minutes..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable gmail.googleapis.com
gcloud services enable analyticsdata.googleapis.com
gcloud services enable analyticsadmin.googleapis.com

# 3. Build the Docker image using Cloud Build

Write-Host " Step 3: Building Docker image with Cloud Build..." -ForegroundColor Cyan
Write-Host "This will take several minutes..."
gcloud builds submit --tag $IMAGE_NAME .

# 4. Deploy to Cloud Run

Write-Host "🚢 Step 4: Deploying to Cloud Run..." -ForegroundColor Cyan
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --timeout 300 `
    --set-env-vars "GA4_MCP_SERVER_URL=$GA4_MCP_SERVER_URL,SENDER_EMAIL=noreply@avisia.fr,GMAIL_OAUTH_CLIENT_ID=$GMAIL_OAUTH_CLIENT_ID,GMAIL_OAUTH_CLIENT_SECRET=$GMAIL_OAUTH_CLIENT_SECRET,GMAIL_OAUTH_REFRESH_TOKEN=$GMAIL_OAUTH_REFRESH_TOKEN" `
    --max-instances 10 `
    --min-instances 0

# 5. Get the service URL
Write-Host ""
Write-Host "📍 Step 5: Getting service URL..." -ForegroundColor Cyan
$SERVICE_URL = gcloud run services describe $SERVICE_NAME `
    --platform managed `
    --region $REGION `
    --format 'value(status.url)'

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Test the service: Invoke-WebRequest -Uri '$SERVICE_URL/test' -Method POST"
Write-Host "2. Run .\setup_scheduler.ps1 to configure Cloud Scheduler"
Write-Host "3. Check the logs: gcloud logging read 'resource.labels.service_name=$SERVICE_NAME' --limit 50"
Write-Host ""
Write-Host "Recipients who will receive reports:"
Write-Host "  - mjacobson@avisia.fr"
Write-Host "  - mnunez@avisia.fr"
Write-Host "  - adejullien@avisia.fr"

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
