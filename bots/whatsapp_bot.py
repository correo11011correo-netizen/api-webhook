from flask import Flask, request, jsonify
import sys
import logging

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

# --- Identidad del Bot ---
BOT_NAME = "WhatsApp Bot Placeholder"
BOT_TYPE = "whatsapp_placeholder"

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para que el Manager verifique el estado y la identidad del bot."""
    logging.info("Health check solicitado por el Manager.")
    return jsonify({
        "status": "ok",
        "name": BOT_NAME,
        "type": BOT_TYPE
    })

@app.route('/', methods=['POST'])
def handle_webhook():
    """Endpoint principal que recibe el webhook redirigido por el Manager."""
    port = request.environ.get('SERVER_PORT', 'N/A')
    logging.info(f"Webhook recibido en puerto {port}: {request.json}")
    return jsonify({"status": "received", "bot_name": BOT_NAME}), 200

if __name__ == '__main__':
    if len(sys.argv) > 1:
        port_num = int(sys.argv[1])
        logging.info(f"Iniciando '{BOT_NAME}' en el puerto {port_num}")
        app.run(host='0.0.0.0', port=port_num)
    else:
        logging.error(f"Error: Debes especificar un puerto. Uso: python {sys.argv[0]} <puerto>")
        sys.exit(1)