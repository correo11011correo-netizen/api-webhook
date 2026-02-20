from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import json
import requests
import logging
import socket

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [Port-Monitor] [%(levelname)s] %(message)s')

# --- Configuración de la Aplicación ---
app = Flask(__name__)
CORS(app) # Habilitar CORS para todas las rutas

# --- Carga de Configuración ---
def load_config():
    """Carga la configuración de los servicios a monitorear desde config.json."""
    try:
        with open('config.json') as f:
            logging.info("Cargando configuración de servicios desde config.json")
            # --- !! LÍNEA CORREGIDA !! ---
            return json.load(f)
    except Exception as e:
        logging.error(f"No se pudo cargar o parsear config.json: {e}")
        return {"services": []}

CONFIG = load_config()

# --- Lógica de Diagnóstico de Puertos ---
def check_service_status(service_config):
    """
    Verifica el estado de un servicio. Primero revisa el puerto, luego el endpoint /health.
    Retorna un diccionario con el estado y la información del servicio.
    """
    port = service_config["port"]
    status_info = {
        "config": service_config,
        "state": "Inactivo", # Estado por defecto
        "service_name": service_config["name"],
        "service_type": "N/A"
    }

    # Paso 1: Verificar si el puerto está abierto
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    if s.connect_ex(("127.0.0.1", port)) != 0:
        s.close()
        return status_info # Retorna "Inactivo" si el puerto está cerrado
    s.close()

    # Paso 2: Si el puerto está abierto, intentar obtener el health check
    try:
        response = requests.get(f'http://127.0.0.1:{port}/health', timeout=1)
        if response.status_code == 200:
            service_data = response.json()
            status_info["state"] = "Activo"
            status_info["service_name"] = service_data.get("name", "Nombre Desconocido")
            status_info["service_type"] = service_data.get("type", "Tipo Desconocido")
        else:
            status_info["state"] = "No Responde"
    except requests.RequestException:
        status_info["state"] = "No Responde"
        
    return status_info

# --- Rutas de la Aplicación ---

@app.route('/', methods=['GET'])
def dashboard():
    """Muestra el dashboard con el estado detallado de todos los servicios configurados."""
    service_statuses = [check_service_status(svc) for svc in CONFIG.get("services", [])]
    return render_template('index.html', services=service_statuses)

@app.route('/api/status', methods=['GET'])
def api_status():
    """Endpoint de API que devuelve el estado de todos los servicios en formato JSON."""
    service_statuses = [check_service_status(svc) for svc in CONFIG.get("services", [])]
    # Limpiar la respuesta para la API, eliminando el objeto de configuración interno
    api_response = [
        {"name": s["service_name"], "port": s["config"]["port"], "state": s["state"], "type": s["service_type"]}
        for s in service_statuses
    ]
    return jsonify(api_response)

if __name__ == '__main__':
    logging.info("Iniciando Port-Monitor en modo de desarrollo.")
    app.run(host='0.0.0.0', port=5000)
