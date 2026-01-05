"""
Cloud Run Flask application entry point
Handles HTTP requests from Cloud Scheduler
"""

import os
import logging
from flask import Flask, request, jsonify

from .adk_agent import run_monthly_analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({
        'status': 'healthy',
        'service': 'ga4-analytics-agent',
        'version': '1.0.0'
    }), 200

@app.route('/run', methods=['POST'])
def run_analysis():
    """
    Main endpoint to trigger monthly analysis
    Triggered by Cloud Scheduler via direct HTTP POST
    """
    try:
        logger.info("Received request to run analysis from Cloud Scheduler")

        # Run the monthly analysis (no need to parse request body)
        result = run_monthly_analysis()

        return jsonify({
            'status': 'success',
            'result': result
        }), 200

    except Exception as e:
        logger.error(f"Error running analysis: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint for manual triggering"""
    try:
        result = run_monthly_analysis()
        return jsonify({
            'status': 'success',
            'result': result
        }), 200
    except Exception as e:
        logger.error(f"Error in test endpoint: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
