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
    # FORWARD_URL is now used as a fallback if not defined per bot
    FORWARD_URL = config.get('FORWARD_URL') 
    CONFIGURED_BOTS = config.get('bots', [])
except FileNotFoundError:
    logging.error("FATAL: config.json not found. The service cannot start.")
    exit(1)
except KeyError as e:
    logging.error(f"FATAL: Missing key in config.json: {e}. The service cannot start.")
    exit(1)

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
        
        # Forward to the first enabled bot's URL or the default FORWARD_URL
        target_url = FORWARD_URL
        for bot in CONFIGURED_BOTS:
            if bot.get('enabled'):
                target_url = bot.get('forward_url')
                break
        
        logging.info(f"Received webhook. Forwarding to {target_url}...")
        try:
            requests.post(target_url, json=data, timeout=3)
            logging.info("Webhook forwarded successfully.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to forward webhook: {e}")
        
        return 'OK', 200

# --- Dashboard Endpoint ---
@app.route('/dashboard')
def dashboard():
    """Renders the status dashboard."""
    # 1. Get last request time
    formatted_time = last_webhook_time.strftime('%Y-%m-%d %H:%M:%S UTC') if last_webhook_time else None

    # 2. Get recent logs
    try:
        log_process = subprocess.run(
            ['sudo', 'tail', '-n', '20', '/var/log/apache2/api-fundacion-error.log'],
            capture_output=True, text=True, check=True
        )
        logs = log_process.stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logs = f"Error al leer el log: {e}"

    # 3. Get status of services for enabled bots
    service_status_list = []
    for bot in CONFIGURED_BOTS:
        if bot.get('enabled'):
            service_name = bot.get('service_name')
            if service_name:
                try:
                    status_process = subprocess.run(
                        ['systemctl', 'is-active', service_name],
                        capture_output=True, text=True
                    )
                    status = status_process.stdout.strip()
                except FileNotFoundError:
                    status = 'unknown'
                service_status_list.append({'name': service_name, 'status': status})

    return render_template(
        'status.html',
        last_request_time=formatted_time,
        logs=logs,
        bots=CONFIGURED_BOTS,
        service_status=service_status_list
    )

# --- Health Check Endpoint ---
@app.route('/health', methods=['GET'])
def health_check():
    """A simple endpoint to confirm the service is running."""
    return jsonify({"status": "ok", "name": "api-fundacion-idear-webhook"}), 200

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)