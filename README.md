# Dashboard de Diagnóstico de Puertos

## 1. Propósito

Esta herramienta monitorea en tiempo real una lista de puertos locales y muestra el estado de los servicios que se ejecutan en ellos. Su propósito es actuar como un **dashboard de diagnóstico centralizado** para desarrolladores, permitiendo verificar rápidamente qué servicios están activos y si responden correctamente.

No gestiona webhooks ni redirige tráfico. Su única función es **monitorear y reportar**.

---

## 2. El Contrato de Servicio: Endpoint `/health`

Para que el dashboard pueda identificar un servicio y mostrarlo como **"Activo"**, dicho servicio **DEBE** implementar un endpoint `GET /health`. Este es el contrato que permite el descubrimiento.

-   **Ruta:** `GET /health`
-   **Función:** Debe devolver una respuesta JSON que identifique el servicio.
-   **Respuesta JSON Requerida:**
    ```json
    {
      "name": "Nombre Descriptivo del Servicio (ej. API de Autenticación v2)",
      "type": "Tipo de Servicio (ej. rest-api, whatsapp-bot, etc.)"
    }
    ```

Si un servicio se está ejecutando en un puerto monitoreado pero no implementa este endpoint (o falla), el dashboard lo reportará como **"No Responde"**. Si el puerto está cerrado, se reportará como **"Inactivo"**.

---

## 3. Configuración

Para monitorear tus servicios, edita el archivo `config.json`.

1.  Abre `config.json`.
2.  Añade o modifica los objetos en la lista `services`. Cada objeto requiere dos claves:
    -   `name`: Un nombre descriptivo que se mostrará en el dashboard si el servicio no puede ser identificado.
    -   `port`: El número de puerto que tu servicio está utilizando.

**Ejemplo de `config.json`:**
```json
{
    "services": [
        {
            "name": "Bot Principal (WhatsApp)",
            "port": 5001
        },
        {
            "name": "Nuevo Servicio de Analíticas",
            "port": 8080
        }
    ]
}
```

3.  **Reinicia el Dashboard:** Para que los cambios en `config.json` surtan efecto.
    ```bash
    sudo systemctl restart api_fundacion.service
    ```
4.  **Inicia tu Servicio:** Ejecuta tu aplicación en el puerto configurado. Si implementa el contrato `/health` correctamente, el dashboard lo reflejará como "Activo" al instante.

---

## 4. API de Estado

Para obtener el estado de todos los servicios monitoreados en formato JSON, puedes consultar el siguiente endpoint:

-   **Endpoint:** `GET /api/status`

**Ejemplo (`curl`):**
```bash
curl http://localhost:5000/api/status
```

**Ejemplo de Respuesta:**
```json
[
  {
    "name": "Bot Principal (WhatsApp)",
    "port": 5001,
    "state": "Inactivo",
    "type": "N/A"
  },
  {
    "name": "Servicio de Analíticas Productivas",
    "port": 8080,
    "state": "Activo",
    "type": "data-api"
  }
]
```

---

## 5. Funcionalidad de Webhook Forwarding

Además del monitoreo, esta aplicación puede actuar como un **puente (proxy/forwarder)** para los webhooks de Meta (WhatsApp, Instagram, etc.).

### Propósito

Permite que una única URL pública (`https://api.fundacionidear.com/webhook`) reciba todas las notificaciones de Meta y las reenvíe de forma segura a un servicio de bot interno (como `bot-pagina`) que se ejecuta en un puerto local no expuesto a internet.

### Configuración

Para habilitar el reenvío de webhooks, añade las siguientes claves al `config.json`:

-   `"verify_token"`: El token de verificación secreto que configurarás en la plataforma de desarrolladores de Meta.
-   `"bot_pagina_webhook_url"`: La URL completa (incluyendo el puerto y la ruta) del servicio de bot interno que procesará los mensajes.

**Ejemplo de `config.json` con Webhook:**
```json
{
    "verify_token": "tu-token-secreto-aqui",
    "bot_pagina_webhook_url": "http://127.0.0.1:5001/webhook",
    "services": [
        {
            "name": "Bot Principal (WhatsApp)",
            "port": 5001
        }
    ]
}
```

### Flujo de Funcionamiento

1.  **Verificación (`GET`):** Cuando configuras tu endpoint en la plataforma de Meta, Meta envía una petición `GET` a `https://tu-dominio.com/webhook`. La aplicación verifica que el `hub.verify_token` coincida con el `verify_token` del `config.json` y responde el `hub.challenge`.
2.  **Recepción de Mensajes (`POST`):** Cuando un usuario envía un mensaje a tu bot, Meta envía una petición `POST` con el contenido del mensaje a `https://tu-dominio.com/webhook`.
3.  **Reenvío (`POST`):** La aplicación recibe esta petición e inmediatamente la reenvía al `bot_pagina_webhook_url` configurado.
4.  **Respuesta Rápida:** La aplicación responde `OK` a Meta sin esperar la respuesta del bot interno. Esto asegura que Meta reciba una confirmación rápida y no desactive el webhook por timeouts.