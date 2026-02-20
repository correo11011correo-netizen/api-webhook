from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({'status': 'OK', 'message': 'Servidor de prueba Python activo.'})

@app.route('/api/webhook', methods=['GET'])
def webhook_verify():
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.challenge'):
        if request.args.get('hub.verify_token') == 'bot1234':
            return request.args.get('hub.challenge'), 200
        else:
            return 'Verification token mismatch', 403
    return 'Endpoint de webhook listo.', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
