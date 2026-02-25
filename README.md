# Repositorio de Configuración y Código para el Webhook de `api.fundacionidear.com`

## 1. Visión General del Proyecto

Este repositorio contiene el código de la aplicación y la documentación de la configuración del servidor para el webhook de la API de Meta (WhatsApp), accesible públicamente a través de `https://api.fundacionidear.com/webhook`.

El objetivo de este documento es proporcionar una fuente de verdad clara y estructurada para cualquier desarrollador o agente de IA que necesite entender, mantener o depurar el sistema.

---

## 2. Estructura del Repositorio

- **`/app`**: Contiene el código fuente de la aplicación de backend responsable de procesar los webhooks.
  - `app.py`: La aplicación principal escrita en Flask.
  - `config.example.json`: Una plantilla que muestra las claves de configuración requeridas por `app.py`. **Nota**: El archivo `config.json` real no debe ser subido al repositorio.

- **`/current_configuration`**: Contiene una instantánea de los archivos de configuración críticos extraídos directamente del servidor `mi-servidor-web` en la fecha del último commit.
  - `README.md`: Una explicación detallada de cada archivo en este directorio.
  - `apache_virtualhost.conf`: La configuración del VirtualHost de Apache.
  - `gcp_firewall_rules.json`: Las reglas de firewall de Google Cloud.
  - `python_app_code.py`: Una copia del código de la aplicación que se está ejecutando actualmente.
  - `fullchain.pem` y `privkey.pem`: Los certificados SSL públicos y privados. **ADVERTENCIA**: La clave privada es información sensible.
  - `config.example.json`: Plantilla de configuración.

- **`README.md`**: Este archivo principal.

---

## 3. Guía de Despliegue y Diagnóstico

### 3.1. Requisitos del Servidor

- Una instancia de cómputo con acceso a la red.
- Software instalado: `apache2`, `python3`, `certbot`.
- Un registro DNS (Tipo A) apuntando `api.fundacionidear.com` a la IP pública de la instancia.

### 3.2. Configuración de la Aplicación (`/app`)

1.  **Copiar el código**: Sube el contenido de la carpeta `/app` a la instancia del servidor (ej. `/home/user/api-webhook-app`).
2.  **Crear `config.json`**: Dentro del directorio de la aplicación, crea un archivo `config.json` basándote en `config.example.json`.
    - `VERIFY_TOKEN`: Debe ser una cadena secreta y coincidir exactamente con el token que configures en el panel de desarrolladores de Meta.
    - `FORWARD_URL`: La URL del servicio al que se reenviarán los datos de los webhooks (mensajes).
3.  **Ejecutar la aplicación**: La aplicación `app.py` debe ejecutarse como un servicio persistente que escuche en `0.0.0.0:5000`. Se recomienda usar un gestor de procesos como `gunicorn` o `systemd`.

    **Ejemplo de ejecución con Gunicorn:**
    ```bash
    gunicorn --bind 0.0.0.0:5000 app:app
    ```

### 3.3. Configuración del Servidor Web (Apache)

1.  **Copiar el VirtualHost**: El archivo `deployment_config/apache-api.fundacionidear.com.conf` debe ser copiado a `/etc/apache2/sites-available/`.
2.  **Habilitar el sitio y los módulos**:
    ```bash
    sudo a2ensite apache-api.fundacionidear.com.conf
    sudo a2enmod proxy proxy_http ssl
    sudo systemctl restart apache2
    ```
3.  **Generar Certificados SSL**: Si es la primera vez, genera los certificados con Certbot.
    ```bash
    sudo certbot --apache -d api.fundacionidear.com
    ```
    Certbot modificará automáticamente el archivo de configuración de Apache para usar los certificados.

### 3.4. Diagnóstico Clave (Hallazgo Actual)

- **Causa Raíz del Fallo**: El análisis de la instancia reveló que la aplicación `app.py` no podía iniciarse porque el archivo `config.json` **no existía** en el directorio esperado.
- **Pasos para la Solución**:
    1.  Crear el archivo `config.json` en la ubicación correcta en el servidor.
    2.  Poblarlo con el `VERIFY_TOKEN` y la `FORWARD_URL` correctos.
    3.  Reiniciar el proceso de la aplicación `app.py` para que cargue la nueva configuración.

Una vez que la aplicación se esté ejecutando correctamente, el endpoint `https://api.fundacionidear.com/webhook` responderá adecuadamente a la solicitud de verificación de Meta.
