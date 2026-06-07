# -*- coding: utf-8 -*-
import os 
import sys
import sqlite3
import uuid
import json
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, request, send_from_directory, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv

from global_db import GlobalDatabaseManager

# --- Configuracion de Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WhatsAppAPI")

# --- Rutas absolutas ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) 
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')

BOT_ENGINE_PATH = os.path.join(PROJECT_ROOT, 'bot-manager', 'bot-engine')
DB_PATH = os.path.join(PROJECT_ROOT, 'bot-manager', 'database', 'bot_dashboard.db')

if BOT_ENGINE_PATH not in sys.path:
    sys.path.insert(0, BOT_ENGINE_PATH)

try:
    from engine import load_config, send_msg
except ImportError:
    logger.error("No se pudo importar el motor del bot. Verifica la estructura de carpetas.")
    sys.exit(1)

# Inicializar Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "whatsapp-secret-key-123") 
CORS(app)

# Cargar configuracion
env_path = os.path.join(BOT_ENGINE_PATH, '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
cfg = load_config()

# --- Base de Datos Global (Sincronizada con Stock Pro) ---
try:
    global_db = GlobalDatabaseManager()
    logger.info("Conexion a DB Global establecida.")
except Exception as e:
    logger.critical(f"Fallo critico al conectar con DB Global: {e}")
    global_db = None

def get_db_connection():
    """Conexion a la DB local de WhatsApp (SQLite)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- MIDDLEWARE DE SESION ---
def validate_session():
    token = request.headers.get("Authorization") or request.cookies.get("session_token")
    if not token or not global_db:
        return None
    
    session_data = global_db.fetch_one(
        "SELECT user_data, expires_at FROM sessions WHERE token = %s",
        (token,)
    )
    
    if not session_data:
        return None

    user_data = session_data["user_data"]
    if isinstance(user_data, str):
        user_data = json.loads(user_data)

    expires_at = session_data["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        global_db.execute("DELETE FROM sessions WHERE token = %s", (token,))
        return None

    return user_data

# --- RUTAS DEL FRONTEND ---

@app.route('/')
def serve_hub():
    return send_from_directory(FRONTEND_DIR, 'hub.html')

@app.route('/login.html')
def serve_login():
    return send_from_directory(FRONTEND_DIR, 'login.html')

@app.route('/index.html')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(FRONTEND_DIR, path)

# --- ENDPOINTS DE LA API ---

@app.route('/api/login', methods=['POST'])
def login():
    if not global_db:
        return jsonify({"success": False, "message": "Servidor de autenticacion no disponible"}), 500

    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"success": False, "message": "Usuario y password requeridos"}), 400

    pwd_hash = hash_password(password)

    user = global_db.fetch_one(
        "SELECT u.*, t.plan FROM users u JOIN tenants t ON u.tenant_id = t.id WHERE u.username = %s AND u.password_hash = %s",
        (username, pwd_hash)
    )

    if not user:
        user = global_db.fetch_one(
            "SELECT * FROM users WHERE username = %s AND password_hash = %s AND role = 'MASTER'",
            (username, pwd_hash)
        )

    if not user:
        return jsonify({"success": False, "message": "Credenciales incorrectas"}), 401

    if not user.get("is_active", True):
        return jsonify({"success": False, "message": "Cuenta suspendida"}), 403

    token = str(uuid.uuid4())
    user_data = {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "tenant_id": user.get("tenant_id"),
        "plan": user.get("plan", "FREE")
    }
    
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    global_db.execute(
        "INSERT INTO sessions (token, user_data, expires_at) VALUES (%s, %s, %s)",
        (token, json.dumps(user_data), expires_at)
    )

    return jsonify({"success": True, "token": token, "user": user_data})

@app.route('/api/chats', methods=['GET'])
def get_chats():
    user = validate_session()
    if not user:
        return jsonify({"success": False, "message": "Sesion no valida o expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT
            c.phone_number,
            c.name,
            conv.is_human_intervening,
            MAX(m.timestamp) AS last_message_timestamp,
            (SELECT content FROM messages WHERE contact_id = c.id ORDER BY timestamp DESC LIMIT 1) AS last_message_content
        FROM contacts c
        LEFT JOIN conversations conv ON c.id = conv.contact_id
        LEFT JOIN messages m ON c.id = m.contact_id
        GROUP BY c.id
        ORDER BY last_message_timestamp DESC;
    """
    cursor.execute(query)
    conversations = [dict(row) for row in cursor.fetchall()] 
    conn.close()
    return jsonify(conversations)

@app.route('/api/chats/<phone_number>/messages', methods=['GET'])
def get_messages(phone_number):
    user = validate_session()
    if not user:
        return jsonify({"success": False, "message": "Sesion no valida o expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT m.sender, m.content, m.timestamp
        FROM messages m
        JOIN contacts c ON m.contact_id = c.id
        WHERE c.phone_number = ?
        ORDER BY m.timestamp ASC;
    """
    cursor.execute(query, (phone_number,))
    messages = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT conv.is_human_intervening
        FROM conversations conv 
        JOIN contacts c ON conv.contact_id = c.id
        WHERE c.phone_number = ?
    """, (phone_number,))
    row = cursor.fetchone()
    is_human = bool(row['is_human_intervening']) if row else False

    conn.close()
    return jsonify({"messages": messages, "is_human_intervening": is_human})

@app.route('/api/chats/<phone_number>/toggle', methods=['POST'])
def toggle_bot(phone_number):
    user = validate_session()
    if not user:
        return jsonify({"success": False, "message": "Sesion no valida o expirada"}), 401

    data = request.json
    status = data.get('is_human_intervening', True)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversations (contact_id, is_human_intervening)
        VALUES ((SELECT id FROM contacts WHERE phone_number = ?), ?) 
        ON CONFLICT(contact_id) DO UPDATE SET
        is_human_intervening = excluded.is_human_intervening,
        last_updated = CURRENT_TIMESTAMP;
    """, (phone_number, 1 if status else 0))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "is_human_intervening": status})

@app.route('/api/chats/<phone_number>/send', methods=['POST'])
def send_message(phone_number):
    user = validate_session()
    if not user:
        return jsonify({"success": False, "message": "Sesion no valida o expirada"}), 401

    data = request.json
    message = data.get('message', '').strip()

    if not message:
        return jsonify({"success": False, "message": "Mensaje vacio"}), 400

    try:
        send_msg(cfg, phone_number, message)

        conn = get_db_connection()
        cursor = conn.cursor() 
        cursor.execute("""
            UPDATE messages
            SET sender = 'human'
            WHERE contact_id = (SELECT id FROM contacts WHERE phone_number = ?)
            AND sender = 'bot'
            ORDER BY timestamp DESC LIMIT 1
        """, (phone_number,))
        conn.commit()
        conn.close()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    logger.info(f"Iniciando servidor en puerto {port} (Debug: {debug_mode})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
