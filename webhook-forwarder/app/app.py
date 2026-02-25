from flask import Flask, render_template

app = Flask(__name__)

@app.route("/webhook", methods=["GET","POST"])
def webhook():
    # En una implementación real, aquí se procesaría la lógica del webhook.
    # Por ahora, devuelve una respuesta simple para confirmar que la ruta funciona.
    return "Webhook activo"

@app.route("/dashboard")
def dashboard():
    # Renderiza el template dashboard.html
    return render_template("dashboard.html")

if __name__ == '__main__':
    # Esta sección no se usa cuando se ejecuta con Gunicorn, pero es buena práctica tenerla.
    app.run(host='0.0.0.0', port=5000)
