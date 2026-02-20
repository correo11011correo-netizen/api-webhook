from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

# --- Configuración de la Aplicación ---
app = Flask(__name__)
# Se habilita CORS solo para las rutas bajo /api/ para permitir peticiones desde un frontend
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- Simulación de Verificación de Estado de Servicios ---
# En una aplicación real, estas funciones verificarían conexiones a bases de datos,
# APIs externas, o si los procesos de los bots están activos.

def whatsapp_bot_health_check():
    """Simula una verificación de estado para el Bot de WhatsApp. Siempre retorna True."""
    # Lógica de ejemplo: podría ser ping a un servicio, verificar un PID, etc.
    return True

def data_processor_health_check():
    """Simula una verificación de estado para un procesador de datos. Siempre retorna False."""
    # Lógica de ejemplo: la conexión a la base de datos podría fallar.
    return False


# --- Registro Central de Servicios ---
# Aquí se definen todos los servicios que la API puede gestionar.
# La clave es el identificador del servicio.
SERVICE_REGISTRY = {
    "whatsapp_bot": {
        "name": "Bot de WhatsApp",
        "description": "Recibe y envía mensajes de WhatsApp. Endpoint: /api/webhook",
        "health_check": whatsapp_bot_health_check,
        "handler": None # Aquí iría la función que procesa el mensaje
    },
    "data_processor": {
        "name": "Procesador de Datos",
        "description": "Procesa datos en segundo plano. No disponible actualmente.",
        "health_check": data_processor_health_check,
        "handler": None
    },
}

# --- Rutas de la Aplicación ---

@app.route('/', methods=['GET'])
def dashboard():
    """
    Ruta principal que muestra el dashboard de servicios.
    Realiza una verificación de estado de todos los servicios registrados
    y solo muestra aquellos que están activos.
    """
    active_services = []
    for service_id, service_info in SERVICE_REGISTRY.items():
        if service_info["health_check"]():
            active_services.append(service_info)
    
    return render_template('index.html', services=active_services)

@app.route('/api/webhook', methods=['GET', 'POST'])
def webhook_receiver():
    """
    Endpoint genérico para recibir webhooks (ej. de Meta).
    Verifica si el servicio correspondiente está activo antes de procesar.
    """
    # Se asume que este webhook es para el bot de WhatsApp
    service_id = "whatsapp_bot"
    
    if not SERVICE_REGISTRY[service_id]["health_check"]():
        return jsonify({"status": "error", "message": "Servicio no disponible"}), 503

    if request.method == 'GET':
        # Lógica de verificación del webhook de Meta
        if request.args.get('hub.verify_token') == 'bot124':
            return request.args.get('hub.challenge'), 200
        else:
            return "Token de verificación incorrecto", 403
    
    if request.method == 'POST':
        # Aquí iría la lógica para procesar el mensaje entrante
        data = request.json
        # Ejemplo: SERVICE_REGISTRY[service_id]["handler"](data)
        return jsonify({"status": "success", "message": "Webhook recibido"}), 200

@app.route('/api/status', methods=['GET'])
def api_status():
    """
    Endpoint de API que devuelve el estado de todos los servicios en formato JSON.
    """
    status_report = {}
    for service_id, service_info in SERVICE_REGISTRY.items():
        status_report[service_id] = {
            "name": service_info["name"],
            "active": service_info["health_check"]()
        }
    return jsonify(status_report)

@app.route('/api/send-message', methods=['POST'])
def send_message():
    """
    Endpoint de API para que un frontend envíe un mensaje a través de un bot.
    """
    # Se asume que los mensajes se envían a través del bot de WhatsApp
    service_id = "whatsapp_bot"

    if not SERVICE_REGISTRY[service_id]["health_check"]():
        return jsonify({"status": "error", "message": "Servicio no disponible"}), 503

    data = request.json
    if not data or 'to' not in data or 'text' not in data:
        return jsonify({"status": "error", "message": "Faltan los campos 'to' o 'text'"}), 400

    # Lógica para enviar el mensaje (simulada)
    print(f"Simulando envío de mensaje a {data['to']}: {data['text']}")
    
    return jsonify({"status": "success", "message": "Mensaje enviado (simulado)"})


# --- Arranque de la Aplicación ---
if __name__ == '__main__':
    # Se usa para pruebas locales. En producción, un servidor como Gunicorn lo gestiona.
    app.run(host='0.0.0.0', port=5000)