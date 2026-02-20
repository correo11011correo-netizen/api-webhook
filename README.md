# API Webhook Manager - Guía para Desarrolladores

## 1. Arquitectura General

Este proyecto implementa un patrón de **API Gateway** o **Manager**. Actúa como el único punto de entrada público (`https://api.fundacionidear.com/`) y se encarga de gestionar, monitorear y redirigir el tráfico a múltiples servicios de bots que se ejecutan de forma independiente en procesos locales.

El sistema consta de dos componentes principales:
1.  **El Manager (`app.py`):** La aplicación Flask pública que está activa permanentemente.
2.  **Los Bots (ej. `bots/whatsapp_bot.py`):** Aplicaciones independientes, cada una escuchando en un puerto local, que contienen la lógica específica de un bot.

El **Dashboard de Diagnóstico** en la página principal (`/`) es la herramienta central para monitorear el estado de todos los bots configurados en tiempo real.

---

## 2. El Contrato del Bot: Endpoint `/health`

Para que el Manager pueda reconocer y gestionar un bot, el bot **DEBE** implementar un endpoint `GET /health`. Este es un contrato obligatorio.

-   **Ruta:** `GET /health`
-   **Función:** Debe devolver una respuesta JSON que identifique al bot.
-   **Respuesta JSON Requerida:**
    ```json
    {
      "status": "ok",
      "name": "Nombre Descriptivo del Bot (ej. Bot de Ventas v1.2)",
      "type": "Tipo de Bot (ej. whatsapp, telegram, etc.)"
    }
    ```
El Manager utiliza esta respuesta para poblar el Dashboard de Diagnóstico. Si un bot no implementa este endpoint correctamente, el Manager lo reportará como **"No Responde"**.

---

## 3. Configuración de Nuevos Bots

Para añadir un nuevo bot al sistema, sigue estos pasos:

1.  **Desarrolla tu Bot:** Crea tu aplicación de bot. Asegúrate de que implemente el endpoint `/health` como se describe arriba. Tu bot debe escuchar en un puerto no utilizado (ej. `5004`, `5005`, etc.).

2.  **Edita `config.json`:** Añade un nuevo objeto al array `bots`.
    ```json
    {
        "bots": [
            {
                "id": "whatsapp_pagina_principal",
                "name": "Bot WhatsApp (Página Principal)",
                "type": "whatsapp",
                "port": 5001,
                "verify_token": "TOKEN_SECRETO_PARA_ESTE_BOT",
                "enabled": true
            },
            {
                "id": "nuevo_bot_telegram",
                "name": "Nuevo Bot de Telegram",
                "type": "telegram",
                "port": 5004,
                "enabled": true
            }
        ]
    }
    ```
    -   `id`: Un identificador único. **Se usará en la URL del webhook.**
    -   `name` y `type`: Nombres descriptivos para el dashboard.
    -   `port`: El puerto en el que tu bot estará escuchando.
    -   `verify_token`: (Opcional, para bots tipo WhatsApp) El token que Meta usará para verificar el webhook.
    -   `enabled`: `true` para que el Manager lo gestione, `false` para ignorarlo.

3.  **Reinicia el Manager:** Para que los cambios en `config.json` surtan efecto.
    ```bash
    sudo systemctl restart api_fundacion.service
    ```
4.  **Inicia tu Bot:** Ejecuta tu nuevo bot en el servidor (usando `systemd`, `tmux`, etc.) para que empiece a escuchar en su puerto. Al instante, el Dashboard lo mostrará como **"Activo"**.

---

## 4. Uso de la API y Webhooks

### Webhooks

La URL para configurar en los servicios externos (Meta, Telegram, etc.) sigue un patrón predecible:

-   **Formato:** `https://api.fundacionidear.com/webhook/<bot_id>`
-   **`<bot_id>`:** Corresponde al `id` que definiste en `config.json`.

**Ejemplo (`curl` para simular un webhook de WhatsApp):**
```bash
curl -X POST \
  https://api.fundacionidear.com/webhook/whatsapp_pagina_principal \
  -H 'Content-Type: application/json' \
  -d '{
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "SENDER_ID",
            "changes": [{"value": {"messages": [{"from": "123456789", "text": {"body": "Hola"}}]}}]
        }]
      }'
```

### API de Estado

Para obtener el estado de todos los bots en formato JSON:

-   **Endpoint:** `GET /api/status`

**Ejemplo (`curl`):**
```bash
curl https://api.fundacionidear.com/api/status
```

**Ejemplo de Respuesta:**
```json
{
    "nuevo_bot_telegram": {
        "name": "Nuevo Bot de Telegram",
        "state": "Inactivo",
        "type": "telegram"
    },
    "whatsapp_pagina_principal": {
        "name": "Bot WhatsApp (Página Principal)",
        "state": "Activo",
        "type": "whatsapp"
    }
}
```
