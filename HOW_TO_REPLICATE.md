# Guía Completa: Replicar y Expandir la Arquitectura de Webhooks

Este documento es la guía definitiva para montar desde cero, mantener y expandir la arquitectura de webhooks utilizada en este proyecto.

## Parte 1: Entendiendo la Arquitectura

La solución se divide en dos componentes principales para crear un sistema robusto y flexible:

1.  **Webhook Forwarder (Reenviador)**: Un servicio ligero y seguro expuesto a Internet en el **puerto 5000**. Su única responsabilidad es recibir las solicitudes de Meta, verificar la autenticidad (`GET`) y reenviar el cuerpo de la solicitud (`POST`) al "Bot Engine" activo.
2.  **Bot Engine (Motor del Bot)**: Uno o más servicios internos (en los **puertos 5001, 5002, etc.**) que contienen la lógica de negocio compleja del bot. No están expuestos a Internet y solo reciben peticiones del "Webhook Forwarder".

**Flujo de una Petición de Mensaje (`POST`):**
`Meta API -> Apache (HTTPS:443) -> Webhook Forwarder (HTTP:5000) -> Bot Engine (HTTP:5001)`

---

## Parte 2: Cómo Replicar la Configuración Completa Desde Cero

Sigue estos pasos para montar un servicio idéntico en un nuevo servidor.

### 2.1. Prerrequisitos

- Un dominio o subdominio (ej. `api.tu-dominio.com`).
- Un servidor nuevo (VM) con un SO como Debian 11 y una IP pública.

### 2.2. Paso a Paso

#### 1. Configurar la Infraestructura Base

- **Crear la VM**: En tu proveedor cloud, crea una nueva VM. Al crearla, **permite el tráfico HTTP y HTTPS** en las reglas de firewall.
- **Configurar el DNS**: Crea un **Registro A** en tu proveedor de dominio que apunte tu subdominio (ej. `api`) a la IP pública de tu nueva VM.

#### 2. Instalar el Software en el Servidor

Conéctate a tu nueva VM por SSH y ejecuta:
```bash
# Actualiza la lista de paquetes
sudo apt-get update

# Instala Apache, Python, Pip, Gunicorn y Certbot
sudo apt-get install -y apache2 python3 python3-pip gunicorn certbot python3-certbot-apache
```

#### 3. Desplegar el "Webhook Forwarder" (Servicio Público)

Este es el servicio que se ejecuta en el puerto 5000.

1.  **Crear Directorio y Subir Código**:
    ```bash
    # Crear la carpeta donde vivirá la aplicación
    mkdir -p /home/tu_usuario/webhook-forwarder/app/templates
    
    # Sube los archivos de la carpeta /webhook-forwarder/app del repositorio a este nuevo directorio.
    ```
2.  **Crear `config.json`**:
    - Crea el archivo `/home/tu_usuario/webhook-forwarder/config.json`.
    - Este archivo es CRÍTICO. Le dice al reenviador a qué bot interno debe enviar los mensajes.
      ```json
      {
        "VERIFY_TOKEN": "tu_token_secreto_para_meta",
        "FORWARD_URL": "http://127.0.0.1:5001/webhook" // Apunta al primer Bot Engine
      }
      ```
3.  **Crear el Servicio `systemd` para el Forwarder**:
    - Crea el archivo `/etc/systemd/system/webhook-forwarder.service`.
    - Usa el contenido de `webhook-forwarder/deployment/fundacionidear.service` del repositorio, **ajustando `User` y `WorkingDirectory`** a tus rutas.
4.  **Habilitar y Arrancar el Servicio**:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable webhook-forwarder.service
    sudo systemctl start webhook-forwarder.service
    ```

#### 4. Configurar Apache y SSL

1.  **Crear Configuración de Apache**:
    - Crea un archivo en `/etc/apache2/sites-available/api.tu-dominio.com.conf`.
    - Pega el contenido de `webhook-forwarder/deployment/apache-proxy.conf` del repositorio, **reemplazando `api.fundacionidear.com` por tu propio dominio**.
2.  **Habilitar Módulos y Sitio**:
    ```bash
    sudo a2enmod proxy proxy_http ssl rewrite
    sudo a2ensite api.tu-dominio.com.conf
    sudo systemctl restart apache2
    ```
3.  **Generar Certificado SSL con Certbot**:
    ```bash
    # Reemplaza con tu dominio y correo
    sudo certbot --apache -d api.tu-dominio.com --email tu-correo@ejemplo.com --agree-tos --no-eff-email --redirect
    ```
    Certbot obtendrá el certificado y actualizará automáticamente tu configuración de Apache para usar HTTPS.

En este punto, ya tienes el "Webhook Forwarder" funcionando y expuesto de forma segura.

---

## Parte 3: Cómo Integrar un Nuevo Bot

Esta arquitectura facilita la adición de nuevos bots sin tocar la configuración pública.

### 3.1. Ejemplo: Añadir un Bot de Telegram en el Puerto 5002

**1. Desarrollar el Nuevo Bot**
- Crea tu aplicación de bot (ej. en Flask, FastAPI).
- Asegúrate de que escuche en `127.0.0.1` en un **puerto nuevo y único** (ej. `5002`).
- Debe tener una ruta para recibir los webhooks (ej. `/telegram-webhook`).

**2. Desplegar el Nuevo Bot en la VM**
1.  **Subir Código**: Sube el código de tu nuevo bot a su propio directorio (ej. `/home/tu_usuario/telegram-bot`).
2.  **Crear Entorno Virtual**: Dentro de ese directorio, crea un entorno virtual e instala sus dependencias.
    ```bash
    cd /home/tu_usuario/telegram-bot
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **Crear Servicio `systemd`**:
    - Crea un nuevo archivo de servicio (ej. `/etc/systemd/system/telegram-bot.service`).
    - Puedes usar `deployment-examples/new-telegram-bot.service.example` del repositorio como plantilla.
    - **Ajusta `WorkingDirectory` y `ExecStart`** para que apunten a tu nuevo bot, a su entorno virtual y al puerto `5002`.
      ```ini
      # ...
      WorkingDirectory=/home/tu_usuario/telegram-bot
      ExecStart=/home/tu_usuario/telegram-bot/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5002 main:app
      # ...
      ```
4.  **Habilitar y Arrancar el Nuevo Servicio**:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable telegram-bot.service
    sudo systemctl start telegram-bot.service
    ```

**3. Activar el Nuevo Bot (El Paso Final)**
Para que el "Webhook Forwarder" empiece a enviar mensajes a tu nuevo bot, solo necesitas hacer un cambio.

1.  **Editar `config.json` del Forwarder**:
    ```bash
    sudo nano /home/tu_usuario/webhook-forwarder/config.json
    ```
2.  **Actualizar la `FORWARD_URL`**:
    ```json
    {
      "VERIFY_TOKEN": "tu_token_secreto_para_meta",
      "FORWARD_URL": "http://127.0.0.1:5002/telegram-webhook" // <-- ¡Aquí está el cambio!
    }
    ```
3.  **Reiniciar el Servicio del Forwarder**:
    ```bash
    sudo systemctl restart webhook-forwarder.service
    ```

¡Listo! El sistema ahora reenviará todos los webhooks entrantes a tu nuevo bot de Telegram sin haber modificado la configuración de Apache ni haber expuesto un nuevo puerto a Internet. Para volver al bot anterior, simplemente revierte el cambio en `config.json` y reinicia el servicio.
