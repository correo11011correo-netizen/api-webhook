# Repositorio de Aplicación y Configuración para el Webhook de Meta API

## 1. Visión General del Proyecto

Este repositorio contiene todo lo necesario para desplegar un **endpoint de webhook funcional para la API de Meta (WhatsApp)**. La arquitectura consiste en un servidor web **Apache2** actuando como proxy inverso frente a una aplicación backend escrita en **Flask (Python)**.

- **Endpoint Público**: `https://api.fundacionidear.com/webhook`
- **Servidor**: `mi-servidor-web` en Google Cloud
- **Dirección IP**: `136.113.85.228`

---

## 2. Estructura del Repositorio

- **`/app`**: Contiene el código fuente de la aplicación Flask.
  - `app.py`: La aplicación principal que recibe, verifica y reenvía los webhooks.
  - `config.example.json`: Una plantilla de la configuración requerida por `app.py`.

- **`/deployment`**: Contiene los archivos de configuración exactos y funcionales del servidor.
  - `fundacionidear.service`: El archivo de servicio `systemd` que asegura que la aplicación Flask se ejecute de forma persistente.
  - `apache-api.fundacionidear.com.conf`: El archivo de VirtualHost de Apache que configura el proxy inverso y la terminación SSL.

- **`README.md`**: Este archivo, que sirve como guía completa.

---

## 3. Guía de Despliegue (Desde Cero)

Sigue estos pasos para replicar la configuración en un nuevo servidor Debian/Ubuntu.

### Paso 3.1: Configuración Inicial del Servidor

1.  **Instalar Software Necesario**:
    ```bash
    sudo apt-get update
    sudo apt-get install -y apache2 python3 python3-flask python3-requests certbot python3-certbot-apache
    ```

2.  **Configurar Firewall (si aplica)**: Asegúrate de que los puertos 80 y 443 estén abiertos para el tráfico entrante.

### Paso 3.2: Despliegue de la Aplicación Flask

1.  **Crear Directorio de la Aplicación**:
    ```bash
    mkdir -p /home/nestorfabianriveros2014/api-fundacion-idear-webhook
    ```

2.  **Subir Código de la Aplicación**: Copia el contenido de la carpeta `/app` de este repositorio a la carpeta recién creada en el servidor.

3.  **Crear el Archivo de Configuración Real**:
    - Crea un archivo llamado `config.json` en `/home/nestorfabianriveros2014/api-fundacion-idear-webhook/`.
    - Basándote en `app/config.example.json`, llénalo con tus valores reales:
      ```json
      {
        "VERIFY_TOKEN": "fundacionidear2026",
        "FORWARD_URL": "https://api.fundacionidear.com/procesar"
      }
      ```

4.  **Configurar el Servicio `systemd`**:
    - Copia el archivo `deployment/fundacionidear.service` a `/etc/systemd/system/fundacionidear.service` en el servidor.
    - Habilita e inicia el servicio:
      ```bash
      sudo systemctl daemon-reload
      sudo systemctl enable fundacionidear.service
      sudo systemctl start fundacionidear.service
      ```
    - Verifica que esté corriendo: `sudo systemctl status fundacionidear.service`.

### Paso 3.3: Configuración de Apache como Proxy Inverso

1.  **Subir Configuración del VirtualHost**:
    - Copia el archivo `deployment/apache-api.fundacionidear.com.conf` a `/etc/apache2/sites-available/` en el servidor.

2.  **Habilitar Módulos y el Sitio**:
    ```bash
    sudo a2enmod proxy proxy_http ssl rewrite
    sudo a2ensite apache-api.fundacionidear.com.conf
    sudo systemctl restart apache2
    ```

3.  **Generar Certificado SSL**:
    - Asegúrate de que tu DNS (un registro `A` para `api.fundacionidear.com` apuntando a la IP de tu servidor) esté configurado y propagado.
    - Ejecuta Certbot:
      ```bash
      sudo certbot --apache -d api.fundacionidear.com
      ```
    - Certbot detectará el VirtualHost y lo modificará para usar HTTPS. El archivo final se parecerá al contenido de `apache-api.fundacionidear.com.conf` en este repositorio.

---

## 4. Contenido de los Archivos

### `app/app.py`
La aplicación Flask define dos rutas:
- `/webhook` (`GET`, `POST`): Maneja la verificación y el reenvío de webhooks.
- `/health` (`GET`): Un endpoint para verificar que la aplicación está viva.

### `deployment/fundacionidear.service`
Un servicio `systemd` que:
- Ejecuta la aplicación como el usuario `nestorfabianriveros2014`.
- Establece el directorio de trabajo correcto.
- Asegura que la aplicación se reinicie automáticamente si falla (`Restart=always`).

### `deployment/apache-api.fundacionidear.com.conf`
La configuración de Apache que:
- Escucha en el puerto 443 para `api.fundacionidear.com`.
- Maneja los certificados SSL.
- Actúa como proxy, reenviando todo el tráfico a `http://127.0.0.1:5000`.