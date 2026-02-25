# Resumen de Configuración Actual para Webhook

Este directorio contiene una instantánea de los archivos y configuraciones clave que gestionan el endpoint `https://api.fundacionidear.com/webhook` al 25 de febrero de 2026. Está diseñado para ser analizado por agentes de IA y desarrolladores para diagnosticar el estado actual del sistema.

---

## 1. `apache_virtualhost.conf`

Este archivo es la configuración del VirtualHost de Apache para el dominio `api.fundacionidear.com` que se ejecuta en la instancia de Google Cloud.

- **Función Principal**: Actúa como un **proxy inverso**. Recibe todo el tráfico público en el puerto 443 (HTTPS) y lo reenvía a la aplicación Python que se ejecuta localmente en el puerto 5000.
- **Puntos Clave**:
    - `ServerName api.fundacionidear.com`: Define el dominio que esta configuración maneja.
    - `SSLEngine on`: Habilita el cifrado SSL/TLS.
    - `SSLCertificateFile` y `SSLCertificateKeyFile`: Especifican las rutas a los certificados SSL.
    - `ProxyPass / http://127.0.0.1:5000/`: La directiva crucial que reenvía todo el tráfico (`/`) a la aplicación backend.

---

## 2. `gcp_firewall_rules.json`

Este archivo JSON contiene las reglas del Firewall de Google Cloud Platform (GCP) que se aplican a la instancia.

- **Función Principal**: Controlar qué tipo de tráfico de red puede llegar a la máquina virtual desde internet.
- **Puntos Clave**:
    - Las reglas permiten el tráfico entrante (`ingress`) desde cualquier dirección (`0.0.0.0/0`).
    - Los puertos abiertos explícitamente para el tráfico web son `tcp:80` (HTTP) y `tcp:443` (HTTPS).

---

## 3. `ssl_certificate_files.txt`

Este archivo de texto muestra la estructura de archivos de los certificados SSL/TLS emitidos por Let's Encrypt para `api.fundacionidear.com`.

- **Función Principal**: Confirmar la existencia y las rutas correctas de los archivos de certificado que Apache está configurado para usar.
- **Puntos Clave**:
    - `fullchain.pem`: El certificado público y la cadena de confianza.
    - `privkey.pem`: La clave privada del certificado.
    - Los archivos son enlaces simbólicos, una práctica estándar de Certbot para facilitar las renovaciones.

---

## 4. `python_app_code.py`

Este es el código fuente de la aplicación Python que se ejecuta en el backend (puerto 5000) y recibe el tráfico reenviado por Apache.

- **Función Principal**: Contener la lógica de negocio del webhook.
- **Estado Actual**:
    - El archivo fue copiado de `api-fundacion-idear-webhook/app.py` ya que es el candidato más probable.
    - **Análisis Crítico**: Basado en el comportamiento del servidor (que devuelve un `404 Not Found`), este código **no contiene actualmente una ruta o endpoint definido para `/webhook`** que maneje solicitudes `GET` (para la verificación de Meta) o `POST` (para recibir mensajes).
    - El servidor se basa en el framework Flask (`from flask import Flask`).

---

## 5. `logs/`

Este directorio contiene archivos de log extraídos del servidor para ayudar en el diagnóstico.

- **`apache_error.log`**: Últimas 50 líneas del log de errores de Apache. Contiene información crítica sobre problemas en la configuración o durante el procesamiento de solicitudes.
