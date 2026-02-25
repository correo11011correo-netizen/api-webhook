import json
import logging
import requests
from flask import Flask, request, jsonify

# --- Basic Setup ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

# --- Load Configuration ---
try:
    with open('config.json') as f:
        config = json.load(f)
    VERIFY_TOKEN = config['VERIFY_TOKEN']
    FORWARD_URL = config['FORWARD_URL']
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
    if request.method == 'GET':
        # --- Webhook Verification ---
        if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == VERIFY_TOKEN:
            logging.info("Webhook verification successful!")
            return request.args.get('hub.challenge'), 200
        else:
            logging.warning("Webhook verification failed. Token mismatch.")
            return 'Verification token mismatch', 403

    if request.method == 'POST':
        # --- Message Forwarding ---
        data = request.get_json()
        logging.info(f"Received webhook. Forwarding to {FORWARD_URL}...")
        
        try:
            # Forward the request. We don't wait long for a response.
            requests.post(FORWARD_URL, json=data, timeout=3)
            logging.info("Webhook forwarded successfully.")
        except requests.exceptions.RequestException as e:
            # Log the error, but still return OK to Meta.
            logging.error(f"Failed to forward webhook: {e}")
        
        # Respond to Meta immediately to prevent timeouts.
        return 'OK', 200

# --- Health Check Endpoint ---
@app.route('/health', methods=['GET'])
def health_check():
    """A simple endpoint to confirm the service is running."""
    return jsonify({"status": "ok", "name": "api-fundacion-idear-webhook"}), 200

# --- Main Execution ---
if __name__ == '__main__':
    # Listens on port 5000, accessible from any IP address.
    app.run(host='0.0.0.0', port=5000, debug=False)
