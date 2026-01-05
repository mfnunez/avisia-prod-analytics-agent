# Production Files Documentation

## ✅ Files COPIED to Production (9 files)

### Core Application Files (3 files)
1. **avisia_analytics_agent/__init__.py**
   - **Why**: Python package marker, required for module imports
   - **Purpose**: Makes `avisia_analytics_agent` a valid Python package

2. **avisia_analytics_agent/adk_agent.py**
   - **Why**: Core business logic for monthly analytics
   - **Purpose**: Contains all GA4 data processing, AI insights generation, email sending, and Cloud Storage integration

3. **avisia_analytics_agent/main.py**
   - **Why**: Flask application entry point
   - **Purpose**: Defines HTTP endpoints (/run, /test, /) for Cloud Run service

### Container & Build Configuration (3 files)
4. **Dockerfile**
   - **Why**: Essential for building Docker container
   - **Purpose**: Defines container image with Python 3.11, dependencies, and application code

5. **cloudbuild.yaml**
   - **Why**: Cloud Build configuration
   - **Purpose**: Defines build steps, cache-busting, and deployment to Cloud Run

6. **requirements.txt**
   - **Why**: Python dependency specification
   - **Purpose**: Lists all required packages (google-adk, google-genai, pandas, etc.)

### Deployment Scripts (2 files)
7. **deploy_agent.ps1**
   - **Why**: Automated deployment script
   - **Purpose**: Builds Docker image, deploys to Cloud Run, sets environment variables and secrets

8. **setup_scheduler.ps1**
   - **Why**: Cloud Scheduler configuration
   - **Purpose**: Sets up monthly automated execution via Cloud Scheduler

### Version Control (1 file)
9. **.gitignore**
   - **Why**: Good practice for version control
   - **Purpose**: Prevents committing sensitive files, cache, and build artifacts

---

## ❌ Files NOT COPIED (33 files)

### Sensitive/Secret Files (3 files) - CRITICAL TO EXCLUDE
- **client_secret.json** - OAuth client secrets (NEVER deploy)
- **gmail_oauth_credentials.txt** - Gmail credentials (NEVER deploy)
- **avisia_analytics_agent/.env** - Local environment variables with secrets (NEVER deploy)

### Documentation Files (9 files) - Not needed at runtime
- **README.md** - Project documentation
- **DEPLOYMENT.md** - Deployment guide
- **DEPLOYMENT_WINDOWS.md** - Windows deployment guide
- **DEPLOYMENT_CHECKLIST.md** - Deployment checklist
- **CLOUD_BUILD_SETUP.md** - Cloud Build setup guide
- **GMAIL_OAUTH2_SETUP.md** - Gmail OAuth setup guide
- **ANALYTICS_INTEGRATION.md** - Analytics integration docs
- **LOCAL_TESTING.md** - Local testing guide

### Test Files (6 files) - Development only
- **test_agent.py** - Agent testing script
- **test_deployed_service.py** - Service testing script
- **test_local.py** - Local testing script
- **test_script.ps1** - PowerShell test script
- **test_local.ps1** - Local test script
- **test_env_var.ps1** - Environment variable test
- **test_analytics_reports_report_2025-10-27_to_2025-11-02.json** - Test data

### Setup Utilities (2 files) - Used once during setup, not at runtime
- **get_gmail_refresh_token.ps1** - OAuth token generation utility
- **get_gmail_refresh_token.py** - Python version of token utility

### Build Artifacts (1 file) - Generated during build
- **.cachebust** - Cache busting file for builds

### Template Files (1 file) - Not used in production
- **.env.template** - Environment variable template for developers

### Unused/Alternative Files (5 files)
- **avisia_analytics_agent/agent.py** - Template file, not used in production
- **app.py** - Appears to be unused/test file
- **deploy_agent.sh** - Bash version (PowerShell version is in production)
- **setup_scheduler.sh** - Bash version (PowerShell version is in production)
- **final_deploy_gcloudrun.ps1** - Duplicate/alternative deployment script

### Asset Files (2 files) - Already embedded in code
- **avisia.png** - Logo (already base64-encoded in adk_agent.py)
- **logo_base64.txt** - Logo data (already in adk_agent.py)

### MCP Server Files (3 files) - Separate component, not part of analytics agent
- **mcp-server/Dockerfile** - MCP server container
- **mcp-server/server.py** - MCP server application
- **mcp-server/deploy.sh** - MCP server deployment
- **deploy_mcp_server.ps1** - MCP server deployment (Windows)
- **deploy_mcp_server.sh** - MCP server deployment (Unix)

---

## 🔒 Security Notes

**IMPORTANT**: The following files contain sensitive data and were INTENTIONALLY EXCLUDED:
1. `client_secret.json` - Contains OAuth2 client secrets
2. `gmail_oauth_credentials.txt` - Contains Gmail OAuth tokens
3. `avisia_analytics_agent/.env` - Contains local environment variables

These secrets are managed through:
- **Google Cloud Secret Manager** for production (gmail-oauth-client-id, gmail-oauth-client-secret, gmail-oauth-refresh-token)
- **Environment variables** set during deployment via deploy_agent.ps1

---

## 📦 Production Directory Structure

```
avisia-prod-analytics-agent/
├── avisia_analytics_agent/
│   ├── __init__.py           # Python package marker
│   ├── adk_agent.py          # Core analytics logic
│   └── main.py               # Flask entry point
├── .gitignore                # Git ignore patterns
├── cloudbuild.yaml           # Cloud Build configuration
├── deploy_agent.ps1          # Deployment script
├── Dockerfile                # Container configuration
├── requirements.txt          # Python dependencies
└── setup_scheduler.ps1       # Scheduler setup
```

---

## 🚀 Deployment Instructions

From the production directory:

1. **Set Gmail OAuth credentials** (one-time setup):
   ```powershell
   $env:GMAIL_OAUTH_CLIENT_ID = 'your-client-id'
   $env:GMAIL_OAUTH_CLIENT_SECRET = 'your-client-secret'
   $env:GMAIL_OAUTH_REFRESH_TOKEN = 'your-refresh-token'
   ```

2. **Deploy to Cloud Run**:
   ```powershell
   .\deploy_agent.ps1
   ```

3. **Setup Cloud Scheduler** (monthly execution):
   ```powershell
   .\setup_scheduler.ps1
   ```

---

## ✨ What This Production Setup Does

- ✅ **Monthly Analytics**: Analyzes previous month's GA4 data (first to last day)
- ✅ **Month-over-Month Comparison**: Calculates evolution rates vs previous month
- ✅ **AI Insights**: Uses Gemini 2.5 Flash for intelligent analysis
- ✅ **Personalized Emails**: Sends customized reports to 5 recipients
- ✅ **Cloud Storage**: Saves analytics data for Streamlit dashboard
- ✅ **Automated Execution**: Runs automatically via Cloud Scheduler
- ✅ **Secure Secrets**: Uses Secret Manager for credentials
- ✅ **Cache-Busted Builds**: Ensures fresh code deployment every time

---

Generated: 2026-01-05
