# Repositorio de Aplicación y Configuración para Webhook de Meta API

## 1. Visión General y Arquitectura

Este repositorio contiene la configuración y el código funcional para el endpoint del webhook de la API de Meta (WhatsApp), accesible públicamente en `https://api.fundacionidear.com`.

La arquitectura de la solución es la siguiente:
**Petición Externa** -> **Apache2 (Proxy Inverso)** -> **Gunicorn (Servidor WSGI)** -> **Flask (Aplicación Python)**

- **Apache2**: Actúa como el servidor web de cara al público. Su función es gestionar el tráfico HTTPS (terminación SSL) y actuar como un proxy inverso, reenviando las peticiones a las rutas correctas hacia el servidor de aplicación interno.
- **Gunicorn**: Es un servidor WSGI de producción para Python. Ejecuta la aplicación Flask de manera robusta y eficiente, gestionando múltiples procesos de trabajo.
- **Flask**: Es el micro-framework de Python que contiene la lógica de la aplicación, definiendo las rutas `/webhook` y `/dashboard`.

---

## 2. Información Clave del Proyecto

- **Proyecto Google Cloud (GCP)**: `My First Project` (ID: `project-2eb71890-6e93-4cfd-a00`)
- **Instancia de Cómputo (VM)**: `mi-servidor-web` (Zona: `us-central1-a`)
- **Dirección IP Pública**: `136.113.85.228`
- **Endpoints Públicos**:
  - `https://api.fundacionidear.com/webhook`
  - `https://api.fundacionidear.com/dashboard`
- **Servicio de Aplicación**: `fundacionidear.service` (Servicio `systemd` que gestiona Gunicorn)
- **Servidor Web**: `apache2.service` (Servicio `systemd`)

---

## 3. Estructura del Repositorio

- **`/app`**: Contiene el código fuente de la aplicación Flask.
  - `app.py`: El código principal de la aplicación con las definiciones de las rutas.
  - `/templates/dashboard.html`: La plantilla HTML para el endpoint del dashboard.
  - `config.example.json`: Una plantilla que muestra las claves de configuración requeridas por `app.py`.

- **`/deployment`**: Contiene los archivos de configuración exactos y funcionales del servidor.
  - `fundacionidear.service`: El archivo de servicio `systemd` que ejecuta Gunicorn.
  - `apache-proxy.conf`: El archivo de VirtualHost de Apache que configura el proxy inverso y SSL.

- **`README.md`**: Este archivo, que sirve como guía completa.

---

## 4. Guía de Mantenimiento y Modificación

### 4.1. Modificar el Código de la Aplicación (Flask)

1.  **Editar Localmente**: Realiza los cambios en `app/app.py` o en los archivos de la carpeta `app/templates/`.
2.  **Subir a la VM**:
    ```bash
    gcloud compute scp --recurse app/ mi-servidor-web:/home/nestorfabianriveros2014/api-fundacion-idear-webhook/ --zone us-central1-a
    ```
3.  **Reiniciar el Servicio de Gunicorn**: Para que los cambios surtan efecto.
    ```bash
    gcloud compute ssh mi-servidor-web --zone us-central1-a -- "sudo systemctl restart fundacionidear.service"
    ```

### 4.2. Modificar la Configuración de Apache

1.  **Editar Localmente**: Realiza los cambios en `deployment/apache-proxy.conf`.
2.  **Subir a la VM**:
    ```bash
    gcloud compute scp deployment/apache-proxy.conf mi-servidor-web:/etc/apache2/sites-available/api.fundacionidear.com-le-ssl.conf --zone us-central1-a
    ```
3.  **Reiniciar Apache**:
    ```bash
    gcloud compute ssh mi-servidor-web --zone us-central1-a -- "sudo systemctl restart apache2"
    ```

### 4.3. Modificar el Servicio de Gunicorn (`systemd`)

1.  **Editar Localmente**: Realiza los cambios en `deployment/fundacionidear.service`.
2.  **Subir a la VM**:
    ```bash
    gcloud compute scp deployment/fundacionidear.service mi-servidor-web:/etc/systemd/system/fundacionidear.service --zone us-central1-a
    ```
3.  **Recargar Daemon y Reiniciar Servicio**:
    ```bash
    gcloud compute ssh mi-servidor-web --zone us-central1-a -- "sudo systemctl daemon-reload && sudo systemctl restart fundacionidear.service"
    ```

---

## 5. Contenido de los Archivos de Configuración

### `deployment/apache-proxy.conf`
_Ubicación en el servidor: `/etc/apache2/sites-available/api.fundacionidear.com-le-ssl.conf`_
```apache
<IfModule mod_ssl.c>
<VirtualHost *:443>
    ServerName api.fundacionidear.com

    SSLEngine On
    SSLCertificateFile /etc/letsencrypt/live/api.fundacionidear.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/api.fundacionidear.com/privkey.pem
    Include /etc/letsencrypt/options-ssl-apache.conf

    # ProxyPass específico para cada ruta
    ProxyRequests Off
    ProxyPreserveHost On
    ProxyPass /webhook http://127.0.0.1:5000/webhook
    ProxyPassReverse /webhook http://127.0.0.1:5000/webhook

    ProxyPass /dashboard http://127.0.0.1:5000/dashboard
    ProxyPassReverse /dashboard http://127.0.0.1:5000/dashboard

    ErrorLog ${APACHE_LOG_DIR}/api-fundacion-error.log
    CustomLog ${APACHE_LOG_DIR}/api-fundacion-access.log combined
</VirtualHost>
</IfModule>
```

### `deployment/fundacionidear.service`
_Ubicación en el servidor: `/etc/systemd/system/fundacionidear.service`_
```ini
[Unit]
Description=Gunicorn instance to serve Fundacion Idear Flask Webhook
After=network.target

[Service]
User=nestorfabianriveros2014
Group=www-data
# Asegurar que el contexto de ejecución sea el correcto para encontrar la carpeta 'templates'
WorkingDirectory=/home/nestorfabianriveros2014/api-fundacion-idear-webhook/app
ExecStart=/usr/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```
