# API Webhook Manager (Proyecto Genérico)

Este proyecto es una plantilla base para desplegar rápidamente un servidor de API y Webhook en Python utilizando Flask. Está diseñado para ser robusto, escalable y fácil de configurar en un nuevo servidor.

El sistema incluye:
- Un **Dashboard Dinámico** que muestra en tiempo real los servicios que están activos.
- Una **API RESTful** con soporte para CORS para interactuar con un frontend.
- Un **Webhook Genérico** para recibir notificaciones de servicios externos como Meta.
- Gestión de procesos mediante **`systemd`** para un funcionamiento continuo.

---

## 1. Requisitos Previos

- Un servidor (ej. una instancia de Google Cloud, AWS, etc.) con acceso `sudo`. Se recomienda una distribución de Linux como Debian o Ubuntu.
- Una dirección IP estática asignada al servidor.
- Un nombre de dominio (o subdominio) apuntando a la IP estática del servidor.
- Python 3 y `pip` instalados en el servidor.
- Git para clonar el repositorio.

---

## 2. Configuración Inicial del Servidor

Estos comandos deben ejecutarse en el nuevo servidor.

### 2.1. Clonar el Repositorio

```bash
git clone <URL_DE_TU_REPOSITORIO_GIT>
cd api-webhook-manager
```

### 2.2. Instalar Paquetes Necesarios

Instalaremos el servidor web Apache y crearemos un entorno virtual para Python.

```bash
# Actualizar e instalar paquetes
sudo apt update && sudo apt upgrade -y
sudo apt install -y apache2 python3-venv

# Crear y activar el entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar las dependencias de Python
pip install -r requirements.txt
```

---

## 3. Configuración del Servidor Web (Proxy Inverso con Apache)

Apache reenviará las peticiones públicas (puertos 80/443) a nuestra aplicación Flask (puerto 5000).

### 3.1. Crear Archivo de Configuración de Apache

```bash
sudo nano /etc/apache2/sites-available/tudominio.com.conf
```

Pega la siguiente configuración (reemplaza `tudominio.com`):

```apache
<VirtualHost *:80>
    ServerName tudominio.com
    ProxyPreserveHost On
    ProxyRequests Off
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/
</VirtualHost>
```

### 3.2. Habilitar Sitio, Módulos y Configurar HTTPS

```bash
# Habilitar módulos, sitio y reiniciar apache
sudo a2enmod proxy proxy_http
sudo a2ensite tudominio.com.conf
sudo systemctl restart apache2

# Instalar certbot y obtener certificado SSL (sigue las instrucciones)
sudo apt install -y certbot python3-certbot-apache
sudo certbot --apache -d tudominio.com
```

---

## 4. Crear el Servicio `systemd`

Esto asegura que la API se ejecute de forma continua.

### 4.1. Crear el Archivo de Servicio

```bash
sudo nano /etc/systemd/system/api_webhook.service
```

Pega la configuración (ajusta `User` y las rutas si es necesario):

```ini
[Unit]
Description=Generic API Webhook Service
After=network.target

[Service]
User=tu_usuario_linux
Group=tu_usuario_linux
WorkingDirectory=/home/tu_usuario_linux/api-webhook-manager
ExecStart=/home/tu_usuario_linux/api-webhook-manager/venv/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 4.2. Habilitar e Iniciar el Servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable api_webhook.service
sudo systemctl start api_webhook.service
sudo systemctl status api_webhook.service
```

---

## 5. Endpoints de la API

Una vez desplegado, el servicio expondrá las siguientes rutas:

### `GET /`
- **Descripción:** Muestra un dashboard HTML con una cuadrícula de todos los servicios que están **actualmente activos** y funcionando.
- **Respuesta:** `text/html`

### `GET /api/status`
- **Descripción:** Devuelve un reporte completo del estado (activo/inactivo) de todos los servicios registrados en formato JSON.
- **Respuesta:** `application/json`
- **Ejemplo de Respuesta:**
  ```json
  {
    "whatsapp_bot": {
      "name": "Bot de WhatsApp",
      "active": true
    },
    "data_processor": {
      "name": "Procesador de Datos",
      "active": false
    }
  }
  ```

### `POST /api/send-message`
- **Descripción:** Permite a un cliente (como un frontend) enviar un mensaje a través del servicio de bot configurado.
- **Requiere CORS:** Sí.
- **Cuerpo de la Petición (JSON):**
  ```json
  {
    "to": "ID_o_numero_de_destino",
    "text": "Este es el mensaje a enviar."
  }
  ```
- **Respuesta de Éxito:**
  ```json
  {
    "status": "success",
    "message": "Mensaje enviado (simulado)"
  }
  ```

### `GET, POST /api/webhook`
- **Descripción:** Endpoint genérico para recibir webhooks de servicios externos. Incluye la lógica de verificación para la API de Meta.
- **Respuesta:** Varía según la petición.