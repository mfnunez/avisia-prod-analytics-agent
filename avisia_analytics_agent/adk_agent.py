"""
ADK Agent for GA4 Monthly Analytics Reports
Connects to GA4 HTTP API, analyzes data, and sends reports via Gmail

Runs monthly to analyze the previous month's acquisition metrics
with special focus on Email and Social media channels.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

from google.adk.agents import Agent
from google.cloud import storage
from google import genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================
# Configuration
# =====================

# Avisia logo embedded as base64
AVISIA_LOGO_BASE64 = "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"

GA4_PROPERTY_ID = "255756835"
RECIPIENTS = ["mjacobson@avisia.fr", "mnunez@avisia.fr", "adejullien@avisia.fr", "btran@avisia.fr","gbertin@avisia.fr"]
GA4_API_URL = os.getenv("GA4_MCP_SERVER_URL", "http://localhost:8080")

# Email configuration (Gmail API)
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@avisia.fr")
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Cloud Storage configuration for Streamlit dashboard
STORAGE_BUCKET_NAME = "avisia-utm-builder"
ANALYTICS_FOLDER = "analytics_reports"

# =====================
# GA4 HTTP API Client
# =====================

class GA4MCPClient:
    """Client to interact with GA4 HTTP API"""

    def __init__(self, server_url: str, property_id: str):
        self.server_url = server_url
        self.property_id = property_id
        logger.info(f"Initialized GA4 HTTP API Client for property {property_id}")

    def run_report(self, start_date: str, end_date: str,
                   dimensions: List[str], metrics: List[str]) -> Dict[str, Any]:
        """
        Run a GA4 report via HTTP API

        Args:
            start_date: Start date in YYYY-MM-DD format or relative (e.g., '7daysAgo')
            end_date: End date in YYYY-MM-DD format or relative (e.g., 'yesterday')
            dimensions: List of dimension names (e.g., ['sessionDefaultChannelGroup'])
            metrics: List of metric names (e.g., ['sessions', 'conversions'])

        Returns:
            Dictionary with report data
        """
        try:
            import requests

            payload = {
                "property_id": self.property_id,
                "start_date": start_date,
                "end_date": end_date,
                "dimensions": dimensions,
                "metrics": metrics
            }

            response = requests.post(
                f"{self.server_url}/run_report",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            # Convert new API format to match expected format
            converted_result = {
                "dimensionHeaders": [{"name": h} for h in result.get("dimension_headers", [])],
                "metricHeaders": [{"name": h} for h in result.get("metric_headers", [])],
                "rows": []
            }

            for row in result.get("rows", []):
                converted_row = {
                    "dimensionValues": [{"value": v} for v in row.get("dimensions", [])],
                    "metricValues": [{"value": v} for v in row.get("metrics", [])]
                }
                converted_result["rows"].append(converted_row)

            return converted_result

        except Exception as e:
            logger.error(f"Failed to fetch GA4 data: {e}")
            raise

# =====================
# Data Processing
# =====================

def process_ga4_response(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process raw GA4 MCP response into structured data

    Returns:
        Dictionary with processed metrics by channel
    """
    if not raw_data or "rows" not in raw_data:
        logger.warning("No data returned from GA4")
        return {}

    processed_data = {
        "channels": [],
        "total_sessions": 0,
        "total_conversions": 0,
        "total_revenue": 0,
        "email_focus": {},
        "social_focus": {}
    }

    for row in raw_data.get("rows", []):
        channel = row.get("dimensionValues", [{}])[0].get("value", "Unknown")
        metrics = row.get("metricValues", [])

        channel_data = {
            "channel": channel,
            "sessions": int(metrics[0].get("value", 0)) if len(metrics) > 0 else 0,
            "conversions": int(metrics[1].get("value", 0)) if len(metrics) > 1 else 0,
            "revenue": float(metrics[2].get("value", 0)) if len(metrics) > 2 else 0,
            "engagement_rate": float(metrics[3].get("value", 0)) if len(metrics) > 3 else 0,
            "avg_session_duration": float(metrics[4].get("value", 0)) if len(metrics) > 4 else 0
        }

        processed_data["channels"].append(channel_data)
        processed_data["total_sessions"] += channel_data["sessions"]
        processed_data["total_conversions"] += channel_data["conversions"]
        processed_data["total_revenue"] += channel_data["revenue"]

        # Special focus on Email and Social channels
        channel_lower = channel.lower()
        if "email" in channel_lower:
            processed_data["email_focus"] = channel_data
        elif "social" in channel_lower or "facebook" in channel_lower or "instagram" in channel_lower:
            processed_data["social_focus"] = channel_data

    # Sort channels by sessions
    processed_data["channels"].sort(key=lambda x: x["sessions"], reverse=True)

    return processed_data

def process_time_series_response(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process time series GA4 data (date + channel dimensions)

    Returns:
        Dictionary with dates and sessions by channel over time
    """
    if not raw_data or "rows" not in raw_data:
        logger.warning("No time series data returned from GA4")
        return {}

    # Collect all data points
    data_by_date_channel = {}
    all_channels = set()

    for row in raw_data.get("rows", []):
        dims = row.get("dimensionValues", [])
        if len(dims) < 2:
            continue

        date = dims[0].get("value", "")
        channel = dims[1].get("value", "Unknown")

        metrics = row.get("metricValues", [])
        sessions = int(metrics[0].get("value", 0)) if len(metrics) > 0 else 0

        if date not in data_by_date_channel:
            data_by_date_channel[date] = {}

        data_by_date_channel[date][channel] = sessions
        all_channels.add(channel)

    # Sort dates
    sorted_dates = sorted(data_by_date_channel.keys())

    # Build series by channel
    series_by_channel = {}
    for channel in all_channels:
        series_by_channel[channel] = []
        for date in sorted_dates:
            sessions = data_by_date_channel.get(date, {}).get(channel, 0)
            series_by_channel[channel].append(sessions)

    return {
        "dates": sorted_dates,
        "by_channel": series_by_channel
    }

def process_campaign_response(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process GA4 campaign data and return sorted list of campaigns

    Returns:
        List of campaign dictionaries sorted by sessions (descending)
    """
    if not raw_data or "rows" not in raw_data:
        logger.warning("No campaign data returned from GA4")
        return []

    campaigns = []
    for row in raw_data.get("rows", []):
        campaign_name = row.get("dimensionValues", [{}])[0].get("value", "Unknown")
        metrics = row.get("metricValues", [])

        # Skip (not set) or empty campaigns
        if campaign_name.lower() in ["(not set)", "(none)", "unknown", ""]:
            continue

        campaign_data = {
            "campaign": campaign_name,
            "sessions": int(metrics[0].get("value", 0)) if len(metrics) > 0 else 0,
        }

        campaigns.append(campaign_data)

    # Sort by sessions descending (highest first)
    campaigns.sort(key=lambda x: x["sessions"], reverse=True)

    return campaigns

def calculate_evolution_rates(current_data: Dict[str, Any], previous_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate month-over-month evolution rates for each channel

    Returns:
        Dictionary with channel names as keys and evolution rates as values (as percentages)
    """
    evolution_rates = {}

    # Create lookup for previous period data
    previous_by_channel = {}
    for ch in previous_data.get("channels", []):
        previous_by_channel[ch["channel"]] = ch["sessions"]

    # Calculate evolution for each current channel
    for ch in current_data.get("channels", []):
        channel_name = ch["channel"]
        current_sessions = ch["sessions"]
        previous_sessions = previous_by_channel.get(channel_name, 0)

        if previous_sessions > 0:
            evolution = ((current_sessions - previous_sessions) / previous_sessions) * 100
            evolution_rates[channel_name] = evolution
        elif current_sessions > 0:
            evolution_rates[channel_name] = 100.0  # New channel, 100% growth
        else:
            evolution_rates[channel_name] = 0.0

    return evolution_rates

# =====================
# Cloud Storage Functions
# =====================

def save_to_cloud_storage(data: Dict[str, Any], period_start: str, period_end: str, insights: str = None):
    """
    Save analytics data to Cloud Storage for Streamlit dashboard

    Args:
        data: Processed analytics data
        period_start: Start date of reporting period
        period_end: End date of reporting period
        insights: AI-generated insights (optional)
    """
    try:
        # Initialize Cloud Storage client
        storage_client = storage.Client()
        bucket = storage_client.bucket(STORAGE_BUCKET_NAME)

        # Prepare data for storage
        report_data = {
            'property_id': GA4_PROPERTY_ID,
            'period_start': period_start,
            'period_end': period_end,
            'generated_at': datetime.now().isoformat(),
            'total_sessions': data.get('total_sessions', 0),
            'total_conversions': data.get('total_conversions', 0),
            'total_revenue': data.get('total_revenue', 0),
            'channels': data.get('channels', []),
            'email_focus': data.get('email_focus', {}),
            'social_focus': data.get('social_focus', {}),
            'ai_insights': insights
        }

        # Create blob name with date range
        blob_name = f"{ANALYTICS_FOLDER}/report_{period_start}_to_{period_end}.json"
        blob = bucket.blob(blob_name)

        # Upload JSON data
        blob.upload_from_string(
            json.dumps(report_data, indent=2),
            content_type='application/json'
        )

        logger.info(f"Analytics data saved to Cloud Storage: {blob_name}")
        return True

    except Exception as e:
        logger.error(f"Failed to save to Cloud Storage: {e}", exc_info=True)
        return False

# =====================
# Report Generation
# =====================

def generate_html_report(data: Dict[str, Any], period_start: str, period_end: str, time_series_data: Dict[str, Any] = None, evolution_rates: Dict[str, float] = None, recipient: str = None, prev_period_start: str = None, prev_period_end: str = None, prev_data: Dict[str, Any] = None, campaign_data: List[Dict[str, Any]] = None) -> str:
    """Generate HTML email report from processed data with Avisia branding"""

    # Use embedded Avisia logo
    logo_base64 = AVISIA_LOGO_BASE64

    if not data or not data.get("channels"):
        return """
        <html>
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        </head>
        <body style="font-family: 'Poppins', sans-serif;">
            <h2>Monthly Analytics Report</h2>
            <p>Aucune donnée disponible pour cette période.</p>
        </body>
        </html>
        """

    # Calculate top performers
    top_channel = data["channels"][0] if data["channels"] else {}

    # Helper function to get evolution for any metric
    def get_channel_metric_evolution(channel_name, metric_name, current_channels, prev_channels):
        """Get evolution rate for a specific channel and metric"""
        if not prev_channels:
            return 0.0

        # Find current and previous values
        current_ch = next((ch for ch in current_channels if ch['channel'] == channel_name), None)
        prev_ch = next((ch for ch in prev_channels if ch['channel'] == channel_name), None)

        if not current_ch or not prev_ch:
            return 0.0

        curr_val = current_ch.get(metric_name, 0)
        prev_val = prev_ch.get(metric_name, 0)

        if prev_val == 0:
            return 100.0 if curr_val > 0 else 0.0
        return ((curr_val - prev_val) / prev_val) * 100

    def format_evolution_inline(evo):
        """Format evolution rate inline with smaller font"""
        if evo > 0:
            return f'<span style="color: #00d4aa; font-size: 11px; margin-left: 5px;">↗ +{evo:.0f}%</span>'
        elif evo < 0:
            return f'<span style="color: #ff6b9d; font-size: 11px; margin-left: 5px;">↘ {evo:.0f}%</span>'
        else:
            return '<span style="color: #999; font-size: 11px; margin-left: 5px;">→ 0%</span>'

    # Get previous channels data
    prev_channels = prev_data.get("channels", []) if prev_data else []

    # Generate channel rows (with evolution rates per metric)
    channel_rows = ""
    for ch in data["channels"]:
        channel_name = ch['channel']

        # Calculate evolution for each metric
        sessions_evo = get_channel_metric_evolution(channel_name, 'sessions', data["channels"], prev_channels)
        conversions_evo = get_channel_metric_evolution(channel_name, 'conversions', data["channels"], prev_channels)
        engagement_evo = get_channel_metric_evolution(channel_name, 'engagement_rate', data["channels"], prev_channels)

        channel_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{ch['channel']}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right; font-weight: 600;">{ch['sessions']:,}{format_evolution_inline(sessions_evo)}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right; font-weight: 600;">{ch['conversions']:,}{format_evolution_inline(conversions_evo)}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right;">{ch['engagement_rate']:.2%}{format_evolution_inline(engagement_evo)}</td>
        </tr>
        """

    # Calculate evolution rates for email and social focus metrics
    def get_focus_evolution(current, previous, metric):
        """Calculate evolution rate for a specific metric"""
        if not previous or metric not in previous or previous[metric] == 0:
            return 0.0
        curr_val = current.get(metric, 0)
        prev_val = previous.get(metric, 0)
        if prev_val == 0:
            return 100.0 if curr_val > 0 else 0.0
        return ((curr_val - prev_val) / prev_val) * 100

    def format_evolution(evo):
        """Format evolution rate with color and arrow"""
        if evo > 0:
            return f'<span style="color: #00d4aa;">↗ +{evo:.0f}%</span>'
        elif evo < 0:
            return f'<span style="color: #ff6b9d;">↘ {evo:.0f}%</span>'
        else:
            return '<span style="color: #999;">→ 0%</span>'

    # Get previous data for email and social
    prev_email = None
    prev_social = None
    if prev_data:
        prev_email = prev_data.get("email_focus")
        prev_social = prev_data.get("social_focus")

    # Email focus section with evolution rates
    email_section = ""
    if data.get("email_focus"):
        email = data["email_focus"]
        evo_sessions = get_focus_evolution(email, prev_email, 'sessions')
        evo_conversions = get_focus_evolution(email, prev_email, 'conversions')
        evo_engagement = get_focus_evolution(email, prev_email, 'engagement_rate')

        email_section = f"""
        <div style="background: linear-gradient(135deg, #2ea3f2 0%, #2A25E8 100%); padding: 20px; border-radius: 8px; color: white; flex: 1; margin-right: 10px;">
            <h3 style="margin-top: 0; font-weight: 600;">📧 Focus Canal Email</h3>
            <p style="margin: 8px 0;"><strong>Sessions :</strong> {email['sessions']:,} {format_evolution(evo_sessions)}</p>
            <p style="margin: 8px 0;"><strong>Conversions :</strong> {email['conversions']:,} {format_evolution(evo_conversions)}</p>
            <p style="margin: 8px 0;"><strong>Taux d'Engagement :</strong> {email['engagement_rate']:.2%} {format_evolution(evo_engagement)}</p>
        </div>
        """

    # Social media focus section with evolution rates
    social_section = ""
    if data.get("social_focus"):
        social = data["social_focus"]
        evo_sessions = get_focus_evolution(social, prev_social, 'sessions')
        evo_conversions = get_focus_evolution(social, prev_social, 'conversions')
        evo_engagement = get_focus_evolution(social, prev_social, 'engagement_rate')

        social_section = f"""
        <div style="background: linear-gradient(135deg, #2ea3f2 0%, #2A25E8 100%); padding: 20px; border-radius: 8px; color: white; flex: 1; margin-left: 10px;">
            <h3 style="margin-top: 0; font-weight: 600;">📱 Focus Réseaux Sociaux</h3>
            <p style="margin: 8px 0;"><strong>Sessions :</strong> {social['sessions']:,} {format_evolution(evo_sessions)}</p>
            <p style="margin: 8px 0;"><strong>Conversions :</strong> {social['conversions']:,} {format_evolution(evo_conversions)}</p>
            <p style="margin: 8px 0;"><strong>Taux d'Engagement :</strong> {social['engagement_rate']:.2%} {format_evolution(evo_engagement)}</p>
        </div>
        """

    # Combine focus sections horizontally
    focus_sections = ""
    if email_section or social_section:
        focus_sections = f"""
        <div style="display: flex; margin: 20px 0; gap: 20px;">
            {email_section}
            {social_section}
        </div>
        """

    # Generate campaign table HTML
    campaign_table_html = ""
    if campaign_data and len(campaign_data) > 0:
        campaign_rows = ""
        for idx, campaign in enumerate(campaign_data[:10], 1):  # Show top 10 campaigns
            campaign_rows += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: center; font-weight: 600; color: #1d1973;">{idx}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{campaign['campaign']}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right; font-weight: 600;">{campaign['sessions']:,}</td>
            </tr>
            """

        campaign_table_html = f"""
        <div style="margin: 20px 0;">
            <table cellpadding='0' cellspacing='0' width='100%' style='border-collapse: collapse; border: 1px solid #ddd; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden;'>
                <thead>
                    <tr>
                        <th style="padding: 15px 12px; background: linear-gradient(135deg, #1d1973 0%, #2A25E8 100%); color: white; font-weight: 600; text-align: center; width: 80px;">#</th>
                        <th style="padding: 15px 12px; background: linear-gradient(135deg, #1d1973 0%, #2A25E8 100%); color: white; font-weight: 600; text-align: left;">Campagne</th>
                        <th style="padding: 15px 12px; background: linear-gradient(135deg, #1d1973 0%, #2A25E8 100%); color: white; font-weight: 600; text-align: right;">Sessions</th>
                    </tr>
                </thead>
                <tbody>
                    {campaign_rows}
                </tbody>
            </table>
        </div>
        """

    # Extract first name from recipient email for personalization
    recipient_name = "Bonjour"
    if recipient:
        name_part = recipient.split('@')[0]
        # Map known emails to proper names
        name_mapping = {
            'mjacobson': 'Marion',
            'mnunez': 'Mario',
            'adejullien': 'Astrid',
            'btran': 'Bao',
            'gbertin':'Gaetan'
        }
        recipient_name = f"Bonjour {name_mapping.get(name_part, name_part.capitalize())}"

    # Create intro paragraph
    intro_text = f"""
    <div style="background-color: #f0f7ff; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #2ea3f2;">
        <p style="margin: 0 0 10px 0; font-size: 16px; color: #1d1973;"><strong>{recipient_name},</strong></p>
        <p style="margin: 5px 0; color: #1d1973;">
            Voici votre rapport mensuel d'analyse de la performance du site Avisia.fr. du <strong>{period_start}</strong> au <strong>{period_end}</strong>.
        </p>
    </div>
    """

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Poppins', sans-serif;
                color: #1d1973;
                line-height: 1.6;
                margin: 0;
                padding: 0;
                background-color: #f8f9fa;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
            }}
            .header {{
                background: linear-gradient(135deg, #1d1973 0%, #2A25E8 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 700;
            }}
            .header p {{
                margin: 10px 0 0 0;
                opacity: 0.9;
                font-weight: 300;
            }}
            .content {{
                padding: 30px;
            }}
            .summary {{
                background-color: #f0f7ff;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                border-left: 4px solid #2ea3f2;
            }}
            .summary h2 {{
                margin-top: 0;
                color: #1d1973;
                font-weight: 600;
                font-size: 22px;
            }}
            .summary p {{
                margin: 10px 0;
            }}
            .chart-container {{
                margin: 30px 0;
                padding: 20px;
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background-color: white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                border-radius: 8px;
                overflow: hidden;
            }}
            th {{
                background: linear-gradient(135deg, #1d1973 0%, #2A25E8 100%);
                color: white;
                padding: 15px 12px;
                text-align: left;
                font-weight: 600;
            }}
            tr:hover {{
                background-color: #f8f9fa;
            }}
            .footer {{
                margin-top: 30px;
                padding: 20px 30px;
                background-color: #f8f9fa;
                font-size: 12px;
                color: #666;
            }}
            .signature {{
                margin-top: 30px;
                padding: 20px;
                border-top: 2px solid #2ea3f2;
                font-size: 14px;
            }}
            .ps {{
                margin-top: 15px;
                font-size: 12px;
                color: #666;
                font-style: italic;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            {f'''<div style="background: linear-gradient(135deg, #1d1973 0%, #2ea3f2 100%);
                        padding: 2rem;
                        border-radius: 0px;
                        text-align: center;
                        margin-bottom: 0;">
                <img src="data:image/png;base64,{logo_base64}" alt="Avisia Logo" style="width: 300px; max-width: 100%; height: auto; display: block; margin: 0 auto;">
            </div>''' if logo_base64 else ''}
            <div class="header">
                <h1>Monthly Analytics Report</h1>
                <p>Période : {period_start} au {period_end}</p>
            </div>

            <div class="content">
                {intro_text}

                <div class="summary">
                    <h2>Résumé Exécutif</h2>
                    <p><strong>Nombre total de sessions :</strong> {data['total_sessions']:,} {format_evolution_inline(((data['total_sessions'] - prev_data.get('total_sessions', 0)) / prev_data.get('total_sessions', 1)) * 100 if prev_data and prev_data.get('total_sessions', 0) > 0 else 0)}</p>
                    <p><strong>Nombre total de conversions* :</strong> {data['total_conversions']:,} {format_evolution_inline(((data['total_conversions'] - prev_data.get('total_conversions', 0)) / prev_data.get('total_conversions', 1)) * 100 if prev_data and prev_data.get('total_conversions', 0) > 0 else 0)}</p>
                    <p><strong>Canal qui génère le plus de trafic :</strong> {top_channel.get('channel', 'N/A')}
                       ({top_channel.get('sessions', 0):,} sessions)</p>
                </div>

                {focus_sections}

                <div class="chart-container">
                    <h3 style="margin-top: 0; color: #1d1973; font-weight: 600;">📈 Évolution des Sessions par Campagne</h3>
                    {campaign_table_html if campaign_table_html else '<p style="color: #666; font-style: italic;">Aucune donnée de campagne disponible pour cette période.</p>'}
                </div>

                <h2 style="color: #1d1973; font-weight: 600; margin-top: 40px;">🧮 Zoom sur les résultats par canal et leurs évolutions par rapport au mois précédent</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Canal</th>
                            <th style="text-align: right;">Sessions</th>
                            <th style="text-align: right;">Conversions</th>
                            <th style="text-align: right;">Taux d'Engagement</th>
                        </tr>
                    </thead>
                    <tbody>
                        {channel_rows}
                    </tbody>
                </table>

                <div class="signature">
                    <p style="margin: 5px 0;">Bien cordialement,</p>
                    <p style="margin: 5px 0; font-weight: 600; color: #2ea3f2;">La Practice Digitale</p>
                    <div class="ps">
                        <p>P.S. : Pour toute question, contactez Mario Nuñez 🙏</p>
                    </div>
                </div>
            </div>
            <div class="footer">
                <p>🤖 Rapport automatisé généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
                <p>Propulsé par Google Analytics 4 et Vertex AI</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html

# =====================
# Email Sending Functions
# =====================

def send_email_simple(to: str, subject: str, body: str, is_html: bool = True) -> dict:
    """
    Send email using Gmail API

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (HTML or plain text)
        is_html: Whether body is HTML

    Returns:
        Dictionary with result
    """
    try:
        logger.info(f"📧 Preparing to send email to: {to}")
        logger.info(f"📧 Subject: {subject}")

        # Send email using Gmail API
        try:
            # Build Gmail API service with OAuth2 refresh token
            client_id = os.getenv('GMAIL_OAUTH_CLIENT_ID')
            client_secret = os.getenv('GMAIL_OAUTH_CLIENT_SECRET')
            refresh_token = os.getenv('GMAIL_OAUTH_REFRESH_TOKEN')

            if not all([client_id, client_secret, refresh_token]):
                raise ValueError(
                    "Missing OAuth2 credentials. Please set GMAIL_OAUTH_CLIENT_ID, "
                    "GMAIL_OAUTH_CLIENT_SECRET, and GMAIL_OAUTH_REFRESH_TOKEN environment variables."
                )

            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=client_id,
                client_secret=client_secret,
                scopes=GMAIL_SCOPES
            )

            service = build('gmail', 'v1', credentials=credentials)

            # Create MIME message
            message = MIMEMultipart('alternative')
            message['to'] = to
            # Don't set 'from' field - Gmail API will use authenticated user's email automatically
            message['subject'] = subject

            # Add body
            if is_html:
                mime_text = MIMEText(body, 'html', 'utf-8')
            else:
                mime_text = MIMEText(body, 'plain', 'utf-8')
            message.attach(mime_text)

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send message
            send_result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"✅ Email sent successfully to {to} (Message ID: {send_result.get('id')})")
            return {
                "status": "success",
                "message": f"Email sent to {to}",
                "message_id": send_result.get('id')
            }

        except Exception as gmail_error:
            logger.error(f"Gmail API error: {gmail_error}")
            logger.warning(f"Email to {to} could not be sent")
            return {
                "status": "error",
                "message": f"Gmail API error: {str(gmail_error)}"
            }

    except Exception as e:
        logger.error(f"Error sending email to {to}: {e}")
        raise

# =====================
# AI Insights Generation
# =====================

def markdown_to_html(markdown_text: str) -> str:
    """
    Convert simple markdown to HTML
    Handles: ### headers, **bold**, bullet points (*), and line breaks
    """
    if not markdown_text:
        return ""

    import re

    html = markdown_text

    # Convert **bold** to <strong>bold</strong>
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

    # Convert bullet points (lines starting with * or -) to HTML list items
    lines = html.split('\n')
    converted_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        # Check if line is a header (### or ##)
        if stripped.startswith('### '):
            if in_list:
                converted_lines.append('</ul>')
                in_list = False
            content = stripped[4:]  # Remove '### '
            converted_lines.append(f'<h4 style="color: #2ea3f2; margin: 15px 0 10px 0; font-weight: 600;">{content}</h4>')
        elif stripped.startswith('## '):
            if in_list:
                converted_lines.append('</ul>')
                in_list = False
            content = stripped[3:]  # Remove '## '
            converted_lines.append(f'<h3 style="color: #1d1973; margin: 15px 0 10px 0; font-weight: 600;">{content}</h3>')
        # Check if line is a bullet point
        elif stripped.startswith('* ') or stripped.startswith('- '):
            if not in_list:
                converted_lines.append('<ul style="margin: 10px 0; padding-left: 20px;">')
                in_list = True
            # Remove the bullet marker and wrap in <li>
            content = stripped[2:]  # Remove '* ' or '- '
            converted_lines.append(f'<li style="margin: 5px 0;">{content}</li>')
        else:
            if in_list:
                converted_lines.append('</ul>')
                in_list = False
            if stripped:  # Only add non-empty lines
                converted_lines.append(f'<p style="margin: 10px 0;">{line}</p>')
            else:
                converted_lines.append('<br/>')

    # Close list if still open
    if in_list:
        converted_lines.append('</ul>')

    return '\n'.join(converted_lines)

def generate_insights_with_gemini(prompt: str) -> str:
    """Generate insights using Vertex AI Gemini"""
    try:
        client = genai.Client(
            vertexai=True,
            project=os.getenv('GOOGLE_CLOUD_PROJECT', 'avisia-training'),
            location='europe-west1'
        )
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        logger.warning(f"Failed to generate Gemini insights: {e}")
        return "AI insights generation unavailable. Please review the data manually."

# =====================
# Main Agent
# =====================

# Initialize the ADK Agent (for AI insights generation)
analytics_agent = Agent(
    name="ga4_monthly_reporter",
    model="gemini-2.5-flash",
    description="Analyzes GA4 acquisition data monthly and provides insights",
    instruction="""You are an analytics expert specializing in Google Analytics 4 data.
    Analyze the provided GA4 acquisition channel data and provide insights about:
    1. Overall traffic trends
    2. Top performing channels
    3. Conversion rates by channel
    4. Special focus on Email and Social Media performance
    5. Actionable recommendations for improvement

    Be very concise, data-driven, and provide specific recommendations."""
)

def run_monthly_analysis():
    """Main function to run monthly GA4 analysis and send report"""
    try:
        logger.info("Starting monthly GA4 analysis...")

        # Calculate date range (previous month: first day to last day)
        today = datetime.now()
        # First day of current month
        first_of_current_month = today.replace(day=1)
        # Last day of previous month
        last_day_of_prev_month = first_of_current_month - timedelta(days=1)
        # First day of previous month
        first_day_of_prev_month = last_day_of_prev_month.replace(day=1)

        period_start = first_day_of_prev_month.strftime("%Y-%m-%d")
        period_end = last_day_of_prev_month.strftime("%Y-%m-%d")

        logger.info(f"Analyzing period: {period_start} to {period_end}")

        # Initialize GA4 HTTP API Client
        ga4_client = GA4MCPClient(GA4_API_URL, GA4_PROPERTY_ID)

        # Fetch data from GA4 via HTTP API
        logger.info("Fetching data from GA4 HTTP API...")
        raw_data = ga4_client.run_report(
            start_date=period_start,
            end_date=period_end,
            dimensions=["sessionDefaultChannelGroup"],
            metrics=[
                "sessions",
                "conversions",
                "totalRevenue",
                "engagementRate",
                "averageSessionDuration"
            ]
        )

        # Process the data
        logger.info("Processing GA4 data...")
        processed_data = process_ga4_response(raw_data)

        if not processed_data or not processed_data.get("channels"):
            logger.warning("No data to report")
            return

        # Fetch campaign data
        logger.info("Fetching campaign data...")
        campaign_raw = ga4_client.run_report(
            start_date=period_start,
            end_date=period_end,
            dimensions=["sessionCampaignName"],
            metrics=["sessions"]
        )
        campaign_data = process_campaign_response(campaign_raw)

        # Fetch previous month data for evolution rates
        logger.info("Fetching previous month data for comparison...")
        # Last day of month before previous month
        last_day_of_two_months_ago = first_day_of_prev_month - timedelta(days=1)
        # First day of month before previous month
        first_day_of_two_months_ago = last_day_of_two_months_ago.replace(day=1)

        prev_period_start = first_day_of_two_months_ago.strftime("%Y-%m-%d")
        prev_period_end = last_day_of_two_months_ago.strftime("%Y-%m-%d")

        prev_raw_data = ga4_client.run_report(
            start_date=prev_period_start,
            end_date=prev_period_end,
            dimensions=["sessionDefaultChannelGroup"],
            metrics=[
                "sessions",
                "conversions",
                "totalRevenue",
                "engagementRate",
                "averageSessionDuration"
            ]
        )
        prev_processed_data = process_ga4_response(prev_raw_data)

        # Calculate evolution rates
        logger.info("Calculating evolution rates...")
        evolution_rates = calculate_evolution_rates(processed_data, prev_processed_data)

        # Use Gemini to generate insights (before generating HTML reports)
        logger.info("Generating AI insights...")
        data_summary = json.dumps(processed_data, indent=2)
        evolution_summary = json.dumps(evolution_rates, indent=2)
        insights_prompt = f"""Vous êtes un expert en analytique spécialisé dans Google Analytics 4.
        Analysez ces données GA4 d'acquisition du {period_start} au {period_end}:

        {data_summary}

        Évolutions par rapport au mois précédent:
        {evolution_summary}

        IMPORTANT: Ce site n'est PAS un site e-commerce. Ne mentionnez jamais le revenu (revenue) dans votre analyse car cette métrique n'est pas pertinente. Concentrez-vous uniquement sur les sessions, conversions (formulaires de contact) et taux d'engagement.

        Fournissez en français:
        1. Points forts de la performance
        2. Analyse du canal Email
        3. Analyse des Réseaux Sociaux
        4. 3 recommandations actionnables pour l'amélioration

        Soyez concis, basé sur les données, et fournissez des recommandations spécifiques.
        Répondez uniquement en français.
        Utilisez des titres de section avec ### pour structurer votre réponse.
        """

        insights = generate_insights_with_gemini(insights_prompt)

        # Save data to Cloud Storage for Streamlit dashboard
        logger.info("Saving analytics data to Cloud Storage...")
        save_success = save_to_cloud_storage(processed_data, period_start, period_end, insights)
        if save_success:
            logger.info("✅ Analytics data successfully saved to Cloud Storage")
        else:
            logger.warning("⚠️ Failed to save analytics data to Cloud Storage")

        # Convert markdown insights to HTML once (same for all recipients)
        insights_html = markdown_to_html(insights)

        # Send email via Gmail - generate personalized report for each recipient
        logger.info(f"Sending report to {RECIPIENTS}...")
        subject = f"Monthly Analytics Report - {period_start} au {period_end}"

        for recipient in RECIPIENTS:
            try:
                # Generate HTML report with personalized greeting for this recipient
                logger.info(f"Generating personalized HTML report for {recipient}...")
                html_report = generate_html_report(
                    processed_data,
                    period_start,
                    period_end,
                    time_series_data=None,
                    evolution_rates=evolution_rates,
                    recipient=recipient,
                    prev_period_start=prev_period_start,
                    prev_period_end=prev_period_end,
                    prev_data=prev_processed_data,
                    campaign_data=campaign_data
                )

                # Add insights to email with model info and conversion explanation
                # Insert before the signature section
                email_body = html_report.replace(
                    '<div class="signature">',
                    f'''
            <div style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0f0 100%); padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #2ea3f2;">
                <h2 style="color: #1d1973; margin-top: 0; font-weight: 600;">🧠 Analyse par l'agent IA</h2>
                <div>{insights_html}</div>
                <p style="margin-top: 15px; font-size: 12px; color: #666; font-style: italic;">
                    Généré par le modèle Google Gemini 2.5 Flash
                </p>
            </div>

            <div style="background-color: #f0f7ff; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #2ea3f2;">
                <h4 style="margin-top: 0; color: #1d1973; font-weight: 600;">📌 * À propos des Conversions</h4>
                <p style="margin: 5px 0; color: #1d1973;">
                    Dans ce rapport, les <strong>conversions</strong> font référence à l'événement clé <code style="background-color: #2ea3f2; color: white; padding: 2px 8px; border-radius: 4px; font-weight: 600;">contact-request-form</code> suivi dans Google Analytics 4.
                    Cette métrique indique quand les utilisateurs soumettent le formulaire de demande de contact sur le site web.
                </p>
                <p style="margin: 5px 0; font-size: 12px; color: #666; font-style: italic;">
                    Note : La définition de conversion peut changer dans les futurs rapports.
                </p>
            </div>

            <div class="signature">'''
                )

                result = send_email_simple(
                    to=recipient,
                    subject=subject,
                    body=email_body,
                    is_html=True
                )
                logger.info(f"Email processed for {recipient}: {result}")
            except Exception as e:
                logger.error(f"Failed to process email for {recipient}: {e}")

        logger.info("Monthly GA4 analysis completed successfully!")
        return {
            "status": "success",
            "period": f"{period_start} to {period_end}",
            "total_sessions": processed_data["total_sessions"],
            "recipients": RECIPIENTS
        }

    except Exception as e:
        logger.error(f"Error in monthly analysis: {e}", exc_info=True)
        raise

# =====================
# Entry Point
# =====================

# Cloud Run Job entry point and local testing
if __name__ == "__main__":
    logger.info("Running monthly analysis...")
    result = run_monthly_analysis()
    print(json.dumps(result, indent=2))
