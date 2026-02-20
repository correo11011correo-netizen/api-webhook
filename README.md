# API Webhook Manager (Proyecto Genérico)

Este proyecto es una plantilla base para desplegar rápidamente un servidor de API y Webhook en Python utilizando Flask. Está diseñado para ser robusto, escalable y fácil de configurar en un nuevo servidor.

El servidor web utiliza un proxy inverso (Apache o Nginx) para gestionar las peticiones y un servicio `systemd` para asegurar que la aplicación Python se ejecute de forma continua.

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

Instalaremos el servidor web Apache y crearemos un entorno virtual para Python para mantener las dependencias aisladas.

```bash
# Actualizar el sistema e instalar Apache y las herramientas de Python
sudo apt update && sudo apt upgrade -y
sudo apt install -y apache2 python3-venv

# Crear un entorno virtual y activarlo
python3 -m venv venv
source venv/bin/activate

# Instalar las dependencias del proyecto
pip install -r requirements.txt
```

---

## 3. Configuración del Servidor Web (Proxy Inverso con Apache)

Apache actuará como un proxy inverso. Recibirá las peticiones públicas (en el puerto 80 para HTTP y 443 para HTTPS) y las reenviará a nuestra aplicación Flask, que se ejecutará localmente en un puerto como el 5000.

### 3.1. Crear el Archivo de Configuración de Apache

Crea un nuevo archivo de configuración para tu sitio. Reemplaza `tudominio.com` con tu dominio real.

```bash
sudo nano /etc/apache2/sites-available/tudominio.com.conf
```

Pega la siguiente configuración dentro del archivo. Esta configuración básica redirige todo el tráfico del puerto 80 a la aplicación Flask en el puerto 5000.

```apache
<VirtualHost *:80>
    ServerName tudominio.com
    ServerAdmin webmaster@localhost

    ProxyPreserveHost On
    ProxyRequests Off
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```

### 3.2. Habilitar el Sitio y los Módulos de Proxy

```bash
# Habilitar los módulos necesarios
sudo a2enmod proxy
sudo a2enmod proxy_http

# Habilitar la nueva configuración del sitio
sudo a2ensite tudominio.com.conf

# Deshabilitar el sitio por defecto si es necesario
sudo a2dissite 000-default.conf

# Reiniciar Apache para aplicar los cambios
sudo systemctl restart apache2
```

### 3.3. Configurar HTTPS (Recomendado y Obligatorio para Webhooks)

Usa `certbot` para obtener un certificado SSL/TLS gratuito de Let's Encrypt.

```bash
sudo apt install -y certbot python3-certbot-apache
sudo certbot --apache -d tudominio.com
```
Certbot modificará automáticamente tu archivo de configuración de Apache para manejar HTTPS y la renovación automática del certificado.

---

## 4. Crear el Servicio `systemd`

Para asegurar que la aplicación Flask se inicie automáticamente con el servidor y se reinicie si falla, crearemos un servicio de `systemd`.

### 4.1. Crear el Archivo de Servicio

```bash
sudo nano /etc/systemd/system/api_webhook.service
```

Pega la siguiente configuración. Asegúrate de que las rutas (`WorkingDirectory` y `ExecStart`) y el usuario (`User`) sean correctos para tu servidor. La ruta de `ExecStart` debe apuntar al ejecutable de python **dentro del entorno virtual**.

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
# Recargar systemd para que reconozca el nuevo servicio
sudo systemctl daemon-reload

# Habilitar el servicio para que se inicie en el arranque
sudo systemctl enable api_webhook.service

# Iniciar el servicio inmediatamente
sudo systemctl start api_webhook.service

# Verificar el estado del servicio
sudo systemctl status api_webhook.service
```
Si todo está correcto, deberías ver que el servicio está `active (running)`.

---

## 5. ¡Listo!

Ahora tienes un servidor de API/Webhook robusto y listo para producción. Tu aplicación `app.py` está siendo servida de forma segura a través de Apache y gestionada por `systemd`.
