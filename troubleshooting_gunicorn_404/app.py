import json
import logging
import requests
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify, render_template

# --- Basic Setup ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

# --- Global Variable for Last Request Time ---
last_webhook_time = None

# --- Load Configuration ---
try:
    with open('config.json') as f:
        config = json.load(f)
    VERIFY_TOKEN = config['VERIFY_TOKEN']
    FORWARD_URL = config.get('FORWARD_URL') 
    CONFIGURED_BOTS = config.get('bots', [])
except FileNotFoundError:
    logging.error("FATAL: config.json not found. The service cannot start.")
    config = {}
    VERIFY_TOKEN = "default_token"
    FORWARD_URL = None
    CONFIGURED_BOTS = []
except (KeyError, json.JSONDecodeError) as e:
    logging.error(f"FATAL: Error in config.json: {e}. The service cannot start.")
    config = {}
    VERIFY_TOKEN = "default_token"
    FORWARD_URL = None
    CONFIGURED_BOTS = []

# --- Webhook Endpoint ---
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """
    Handles Meta's webhook requests.
    - GET: Used for the initial verification challenge.
    - POST: Used to receive and forward incoming messages.
    """
    global last_webhook_time
    last_webhook_time = datetime.now()

    if request.method == 'GET':
        if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == VERIFY_TOKEN:
            logging.info("Webhook verification successful!")
            return request.args.get('hub.challenge'), 200
        else:
            logging.warning("Webhook verification failed. Token mismatch.")
            return 'Verification token mismatch', 403

    if request.method == 'POST':
        data = request.get_json()
        
        target_url = FORWARD_URL
        for bot in CONFIGURED_BOTS:
            if bot.get('enabled'):
                target_url = bot.get('forward_url')
                break
        
        logging.info(f"Received webhook. Forwarding to {target_url}...")
        try:
            if target_url:
                requests.post(target_url, json=data, timeout=3)
                logging.info("Webhook forwarded successfully.")
            else:
                logging.warning("No forward URL configured.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to forward webhook: {e}")
        
        return 'OK', 200

# --- Simple Dashboard Endpoint ---
@app.route('/dashboard')
def dashboard():
    """Renders the simple status dashboard."""
    return render_template('dashboard.html')

# --- Health Check Endpoint ---
@app.route('/health', methods=['GET'])
def health_check():
    """A simple endpoint to confirm the service is running."""
    return jsonify({"status": "ok", "name": "api-fundacion-idear-webhook"}), 200

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
