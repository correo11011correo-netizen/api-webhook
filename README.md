# Repositorio de Aplicación y Configuración para el Webhook de Meta API

## 1. Visión General del Proyecto

Este repositorio contiene todo lo necesario para desplegar y mantener un **endpoint de webhook funcional para la API de Meta (WhatsApp)**. La arquitectura consiste en un servidor web **Apache2** actuando como proxy inverso frente a una aplicación backend escrita en **Flask (Python)**.

- **Nombre del Proyecto GCP**: `My First Project` (ID: `project-2eb71890-6e93-4cfd-a00`)
- **Instancia de Cómputo (VM)**: `mi-servidor-web`
- **Dirección IP Pública de la VM**: `136.113.85.228`
- **Endpoint Público del Webhook**: `https://api.fundacionidear.com/webhook`
- **Puerto Interno de la Aplicación Flask**: `5000`
- **Usuario de Ejecución de la Aplicación**: `nestorfabianriveros2014`
- **Directorio de la Aplicación en la VM**: `/home/nestorfabianriveros2014/api-fundacion-idear-webhook`

---

## 2. Estructura del Repositorio

- **`/app`**: Contiene el código fuente de la aplicación Flask.
  - `app.py`: La aplicación principal que recibe, verifica y reenvía los webhooks.
  - `config.example.json`: Una plantilla que muestra las claves de configuración requeridas por `app.py`. **Nota**: El archivo `config.json` real NO debe ser subido al repositorio por seguridad.

- **`/deployment`**: Contiene los archivos de configuración exactos y funcionales del servidor.
  - `fundacionidear.service`: El archivo de servicio `systemd` que asegura que la aplicación Flask se ejecute de forma persistente.
  - `apache-api.fundacionidear.com.conf`: El archivo de VirtualHost de Apache que configura el proxy inverso y la terminación SSL.

- **`README.md`**: Este archivo, que sirve como guía completa y detallada para el despliegue y mantenimiento.

---

## 3. Guía de Despliegue (Desde Cero)

Sigue estos pasos para replicar la configuración en un nuevo servidor Debian/Ubuntu o para realizar una configuración inicial.

### Paso 3.1: Configuración Inicial del Servidor

1.  **Conectarse a la Instancia**: Utiliza `gcloud compute ssh` o tu método preferido.
    ```bash
    gcloud compute ssh mi-servidor-web --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00
    ```

2.  **Instalar Software Necesario**:
    ```bash
    sudo apt-get update
    sudo apt-get install -y apache2 python3 python3-flask python3-requests certbot python3-certbot-apache
    ```

3.  **Configurar Firewall (si aplica)**: Asegúrate de que los puertos 80 y 443 estén abiertos para el tráfico entrante. Esto ya está configurado en tu proyecto GCP.

### Paso 3.2: Despliegue de la Aplicación Flask

1.  **Crear Directorio de la Aplicación**:
    ```bash
    mkdir -p /home/nestorfabianriveros2014/api-fundacion-idear-webhook
    sudo chown nestorfabianriveros2014:nestorfabianriveros2014 /home/nestorfabianriveros2014/api-fundacion-idear-webhook
    ```

2.  **Subir Código de la Aplicación**: Copia el contenido de la carpeta `/app` de este repositorio a la VM.
    ```bash
    gcloud compute scp app/app.py mi-servidor-web:/home/nestorfabianriveros2014/api-fundacion-idear-webhook/app.py --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00
    ```

3.  **Crear el Archivo de Configuración Real (`config.json`)**:
    - Crea un archivo llamado `config.json` en `/home/nestorfabianriveros2014/api-fundacion-idear-webhook/`.
    - Basándote en `app/config.example.json`, llénalo con tus valores reales. Por ejemplo, el contenido actual en la VM es:
      ```json
      {
        "VERIFY_TOKEN": "fundacionidear2026",
        "FORWARD_URL": "https://api.fundacionidear.com/procesar"
      }
      ```
    - Para crearlo en la VM:
      ```bash
      gcloud compute ssh mi-servidor-web --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00 -- "sudo -u nestorfabianriveros2014 bash -c 'cat <<EOF > /home/nestorfabianriveros2014/api-fundacion-idear-webhook/config.json
{
  \"VERIFY_TOKEN\": \"fundacionidear2026\",
  \"FORWARD_URL\": \"https://api.fundacionidear.com/procesar\"
}
EOF' && sudo chmod 644 /home/nestorfabianriveros2014/api-fundacion-idear-webhook/config.json"
      ```

4.  **Configurar el Servicio `systemd`**:
    - Copia el archivo `deployment/fundacionidear.service` a `/etc/systemd/system/fundacionidear.service` en el servidor.
      ```bash
      gcloud compute scp deployment/fundacionidear.service mi-servidor-web:/etc/systemd/system/fundacionidear.service --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00
      ```
    - Habilita e inicia el servicio:
      ```bash
      gcloud compute ssh mi-servidor-web --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00 -- "sudo systemctl daemon-reload && sudo systemctl enable fundacionidear.service && sudo systemctl start fundacionidear.service"
      ```
    - Verifica que esté corriendo: `gcloud compute ssh mi-servidor-web --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00 -- "sudo systemctl status fundacionidear.service"`.

### Paso 3.3: Configuración de Apache como Proxy Inverso

1.  **Subir Configuración del VirtualHost**:
    - Copia el archivo `deployment/apache-api.fundacionidear.com.conf` a `/etc/apache2/sites-available/` en el servidor.
      ```bash
      gcloud compute scp deployment/apache-api.fundacionidear.com.conf mi-servidor-web:/etc/apache2/sites-available/apache-api.fundacionidear.com.conf --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00
      ```

2.  **Habilitar Módulos y el Sitio**:
    ```bash
    gcloud compute ssh mi-servidor-web --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00 -- "sudo a2enmod proxy proxy_http ssl rewrite && sudo a2ensite apache-api.fundacionidear.com.conf && sudo systemctl restart apache2"
    ```

3.  **Generar Certificado SSL (si es la primera vez)**:
    - Asegúrate de que tu DNS (un registro `A` para `api.fundacionidear.com` apuntando a la IP de tu servidor) esté configurado y propagado.
    - Ejecuta Certbot:
      ```bash
      gcloud compute ssh mi-servidor-web --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00 -- "sudo certbot --apache -d api.fundacionidear.com"
      ```
    - Certbot detectará el VirtualHost y lo modificará para usar HTTPS. El archivo final se parecerá al contenido de `apache-api.fundacionidear.com.conf` en este repositorio.

---

## 4. Mantenimiento y Modificación del Servicio

### 4.1. Modificar el Código de la Aplicación (`app/app.py`)

1.  **Editar Localmente**: Realiza los cambios necesarios en `app/app.py` en tu entorno de desarrollo.
2.  **Subir a la VM**:
    ```bash
    gcloud compute scp app/app.py mi-servidor-web:/home/nestorfabianriveros2014/api-fundacion-idear-webhook/app.py --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00
    ```
3.  **Reiniciar el Servicio Flask**: Para que los cambios surtan efecto:
    ```bash
    gcloud compute ssh mi-servidor-web --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00 -- "sudo systemctl restart fundacionidear.service"
    ```

### 4.2. Modificar la Configuración de la Aplicación (`config.json`)

1.  **Editar Localmente (opcional)**: Edita una copia local de `config.json`.
2.  **Subir a la VM**:
    ```bash
    gcloud compute scp config.json mi-servidor-web:/home/nestorfabianriveros2014/api-fundacion-idear-webhook/config.json --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00
    ```
3.  **Reiniciar el Servicio Flask**: Es crucial para que los cambios se carguen:
    ```bash
    gcloud compute ssh mi-servidor-web --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00 -- "sudo systemctl restart fundacionidear.service"
    ```

### 4.3. Modificar la Configuración de Apache (`deployment/apache-api.fundacionidear.com.conf`)

1.  **Editar Localmente**: Realiza los cambios en `deployment/apache-api.fundacionidear.com.conf`.
2.  **Subir a la VM**:
    ```bash
    gcloud compute scp deployment/apache-api.fundacionidear.com.conf mi-servidor-web:/etc/apache2/sites-available/apache-api.fundacionidear.com.conf --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00
    ```
3.  **Reiniciar Apache**: Para que los cambios en el servidor web se apliquen:
    ```bash
    gcloud compute ssh mi-servidor-web --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00 -- "sudo systemctl restart apache2"
    ```

### 4.4. Modificar el Servicio `systemd` (`deployment/fundacionidear.service`)

1.  **Editar Localmente**: Realiza los cambios en `deployment/fundacionidear.service`.
2.  **Subir a la VM**:
    ```bash
    gcloud compute scp deployment/fundacionidear.service mi-servidor-web:/etc/systemd/system/fundacionidear.service --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00
    ```
3.  **Recargar Daemon y Reiniciar Servicio**:
    ```bash
    gcloud compute ssh mi-servidor-web --zone us-central1-a --project project-2eb71890-6e93-4cfd-a00 -- "sudo systemctl daemon-reload && sudo systemctl restart fundacionidear.service"
    ```

---

## 5. Contenido de los Archivos Clave

### `app/app.py`
La aplicación Flask define dos rutas:
- `/webhook` (`GET`, `POST`): Maneja la verificación y el reenvío de webhooks. (Ver contenido completo en el archivo).
- `/health` (`GET`): Un endpoint para verificar que la aplicación está viva. (Ver contenido completo en el archivo).

### `app/config.example.json`
Plantilla que muestra las variables de entorno esperadas por `app.py`:
```json
{
  "VERIFY_TOKEN": "AQUI_VA_TU_TOKEN_DE_VERIFICACION_DE_META",
  "FORWARD_URL": "http://DIRECCION_DONDE_REENVIAR_EL_WEBHOOK"
}
```

### `deployment/fundacionidear.service`
Un servicio `systemd` que ejecuta la aplicación Flask de forma persistente. Configuración clave:
- `User=nestorfabianriveros2014`
- `WorkingDirectory=/home/nestorfabianriveros2014/api-fundacion-idear-webhook`
- `ExecStart=/usr/bin/python3 /home/nestorfabianriveros2014/api-fundacion-idear-webhook/app.py`
- `Restart=always`

### `deployment/apache-api.fundacionidear.com.conf`
La configuración de VirtualHost de Apache para `api.fundacionidear.com`:
- Escucha en el puerto 443 (HTTPS).
- Realiza la terminación SSL y actúa como proxy inverso.
- `ProxyPass / http://127.0.0.1:5000/` y `ProxyPassReverse / http://127.0.0.1:5000/` reenvían el tráfico a la aplicación Flask.

---

## 6. Configuración de Meta Developers

Para configurar el webhook en el panel de Meta Developers:

- **Callback URL**: `https://api.fundacionidear.com/webhook`
- **Verify Token**: `fundacionidear2026` (Este valor DEBE coincidir con el `VERIFY_TOKEN` en `config.json`)
