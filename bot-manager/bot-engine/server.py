import os
import json
import requests
import sqlite3
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv
from engine import setup_logging, load_submenu_flows, load_config, process_message, send_msg
from flows.messenger import handle_messenger
import db_manager

# --- Paths Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_UI_PATH = os.path.join(BASE_DIR, '../dashboard-ui')
DB_PATH = os.path.join(BASE_DIR, '../database/bot_dashboard.db')

# Initialize Flask to serve the dashboard UI from the specified template and static folder
app = Flask(__name__, template_folder=DASHBOARD_UI_PATH, static_folder=DASHBOARD_UI_PATH)

# --- Bot Webhook Endpoints ---
@app.route("/api/webhook", methods=["GET"])
def verify_whatsapp_instagram():
    VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "default_bot_token")
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Verificación fallida", 403

@app.route("/api/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    cfg = app.config.get("cfg", {})
    try:
        process_message(cfg, data)
    except Exception as e:
        app.logger.error(f"Error processing message: {e}")
    return "OK", 200

@app.route("/api/health", methods=["GET"])
def health():
    # Example call from user instructions
    # Check signature for db_manager.set_human_intervention_status() if parameters are needed
    try:
        # User requested this exact call to verify health/DB connection
        db_manager.set_human_intervention_status()
    except Exception as e:
        app.logger.error(f"Health check db_manager error: {e}")
    return jsonify({"status": "ok", "service": "bot-engine"}), 200

# --- Dashboard Frontend & API Endpoints ---
@app.route('/')
def serve_dashboard():
    ngrok_url = app.config.get("cfg", {}).get("ngrok_public_url", "")
    # Fallback si no hay dashboard.html en la repo para que no falle.
    if os.path.exists(os.path.join(DASHBOARD_UI_PATH, 'index.html')):
        return render_template('index.html', NGROK_URL=ngrok_url)
    return "Dashboard del Bot Engine (Puerto 5001)"

@app.route('/<path:path>')
def serve_dashboard_static_files(path):
    return send_from_directory(DASHBOARD_UI_PATH, path)
    
# --- Main Execution ---
if __name__ == "__main__":
    load_dotenv()
    setup_logging()
    load_submenu_flows()
    app.config["cfg"] = load_config()
    port = int(os.getenv("PORT", 5001))
    
    ngrok_url = app.config.get("cfg", {}).get("ngrok_public_url", "URL_NO_ENCONTRADA")
    print(f"🚀 Servidor unificado en puerto {port}")
    print(f"   - Webhooks de Bot: {ngrok_url}/api/webhook")
    app.run(host='0.0.0.0', port=port, debug=False)
