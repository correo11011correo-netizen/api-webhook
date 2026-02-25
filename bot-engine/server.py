import os
import json
import requests
import sqlite3
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv
# from engine import setup_logging, load_submenu_flows, load_config, process_message, send_msg
# from flows.messenger import handle_messenger
# import db_manager

# --- Paths Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_UI_PATH = os.path.join(BASE_DIR, '../dashboard-ui')
DB_PATH = os.path.join(BASE_DIR, '../database/bot_dashboard.db')

# Initialize Flask to serve the dashboard UI from the specified template and static folder
app = Flask(__name__, template_folder=DASHBOARD_UI_PATH, static_folder=DASHBOARD_UI_PATH)

# --- Bot Webhook Endpoints (Simplificado para depuración) ---
@app.route("/api/webhook", methods=["GET"])
def verify_whatsapp_instagram():
    # VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "default_bot_token") # Intentar leer de .env
    # if request.args.get("hub.verify_token") == VERIFY_TOKEN:
    # Lógica simplificada: Siempre devuelve el challenge si el modo es subscribe
    if request.args.get("hub.mode") == "subscribe":
        return request.args.get("hub.challenge")
    return ("Verificación simplificada fallida", 403)

@app.route("/api/webhook", methods=["POST"])
def webhook_whatsapp_instagram():
    # Lógica simplificada: Siempre devuelve OK
    # data = request.get_json()
    # print(f"📩 Webhook POST recibido en puerto 5001: {data}")
    return "OK (Bot Engine)", 200

# --- Dashboard Frontend & API Endpoints (Mantenido sin cambios) ---

# Route to serve the dynamic index.html with the Ngrok URL injected
@app.route('/')
def serve_dashboard():
    # ngrok_url = app.config.get("cfg", {}).get("ngrok_public_url", "")
    # return render_template('index.html', NGROK_URL=ngrok_url)
    return "Dashboard del Bot Engine (Puerto 5001)"

# Route to serve other static files for the dashboard (CSS, JS)
@app.route('/<path:path>')
def serve_dashboard_static_files(path):
    return send_from_directory(DASHBOARD_UI_PATH, path)
    
# ... (otras rutas API del dashboard pueden ser comentadas o simplificadas si causan errores)

# --- Main Execution ---
if __name__ == "__main__":
    load_dotenv()
    # setup_logging() # Comentado para simplificar
    # load_submenu_flows() # Comentado para simplificar
    # app.config["cfg"] = load_config() # Comentado para simplificar
    port = int(os.getenv("PORT", 5000))
    # ngrok_url = app.config.get("cfg", {}).get("ngrok_public_url", "URL_NO_ENCONTRADA")
    print(f"🚀 Servidor unificado en puerto {port}")
    # print(f"   - Webhooks de Bot: {ngrok_url}/api/webhook")
    # print(f"   - Panel de Control: {ngrok_url}")
    app.run(host='0.0.0.0', port=port, debug=False)