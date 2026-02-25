# Repositorio de Arquitectura de Webhooks de Meta API

## 1. Arquitectura y Visión General

Este repositorio documenta y contiene la configuración para una arquitectura de webhooks desacoplada y robusta, diseñada para recibir y procesar webhooks de la API de Meta (WhatsApp, Instagram, etc.).

La arquitectura se divide en dos componentes principales:

1.  **Webhook Forwarder (Reenviador)**: Un servicio ligero y seguro expuesto a Internet. Su única responsabilidad es recibir las solicitudes de Meta, verificar la autenticidad (para `GET`) y reenviar el cuerpo de la solicitud (`POST`) al "Bot Engine" apropiado.
2.  **Bot Engine (Motor del Bot)**: Uno o más servicios internos que contienen la lógica de negocio compleja del bot. Estos servicios no están expuestos a Internet y solo reciben peticiones del "Webhook Forwarder".

**Flujo de una Petición de Mensaje (`POST`):**
`Meta API -> Apache (HTTPS:443) -> Webhook Forwarder (HTTP:5000) -> Bot Engine (HTTP:5001)`

---

## 2. Información Clave del Proyecto

- **Proyecto Google Cloud (GCP)**: `My First Project` (ID: `project-2eb71890-6e93-4cfd-a00`)
- **Instancia de Cómputo (VM)**: `mi-servidor-web`
- **Dirección IP Pública**: `136.113.85.228`
- **Endpoint Público del Webhook**: `https://api.fundacionidear.com/webhook`

---

## 3. Estructura del Repositorio

- **`/webhook-forwarder`**: Contiene el código y la configuración del servicio reenviador.
  - `/app`: El código de la aplicación Flask.
  - `/deployment`: Los archivos de configuración de `systemd` y `Apache` para este servicio.

- **`/bot-engine`**: Contiene el código y la configuración del bot principal actual.
  - `server.py`: El código del bot.
  - `.env.example`: Una plantilla para las variables de entorno que necesita el bot.
  - `/deployment`: El archivo de servicio `systemd` para este bot.

- **`/deployment-examples`**: Contiene plantillas para desplegar nuevos servicios.
  - `new-telegram-bot.service.example`: Un ejemplo de cómo configurar un nuevo bot para Telegram.

- **`README.md`**: Este archivo.

---

## 4. Cómo Añadir un Nuevo Bot (Ej: Telegram en el puerto 5002)

Esta arquitectura facilita la adición de nuevos bots sin modificar la configuración pública.

**Paso 1: Desarrollar el Nuevo Bot**
- Crea tu aplicación de bot (ej. en Flask, FastAPI).
- Asegúrate de que escuche en `127.0.0.1` en un **puerto nuevo y único** (ej. `5002`).
- Debe tener una ruta para recibir los webhooks (ej. `/telegram-webhook`).

**Paso 2: Desplegar el Nuevo Bot en la VM**
1.  Sube el código de tu nuevo bot a su propio directorio (ej. `/home/nestorfabianriveros2014/new-telegram-bot`).
2.  Crea un entorno virtual e instala sus dependencias.
3.  Crea un nuevo servicio `systemd` para él, basándote en `deployment-examples/new-telegram-bot.service.example`.
    - Modifica `WorkingDirectory` y `ExecStart` para apuntar a tu nuevo bot y al puerto `5002`.
4.  Habilita e inicia el nuevo servicio:
    ```bash
    sudo systemctl enable new-telegram-bot.service
    sudo systemctl start new-telegram-bot.service
    ```

**Paso 3: Configurar el Reenviador (`Webhook Forwarder`)**
Esta es la **única modificación** necesaria para activar el nuevo bot.

1.  Conéctate a la VM y edita el archivo de configuración del reenviador:
    ```bash
    nano /home/nestorfabianriveros2014/api-fundacion-idear-webhook/config.json
    ```
2.  Cambia la `FORWARD_URL` para que apunte a tu nuevo bot:
    ```json
    {
      "VERIFY_TOKEN": "fundacionidear2026",
      "FORWARD_URL": "http://127.0.0.1:5002/telegram-webhook"
    }
    ```
3.  Reinicia **únicamente** el servicio del reenviador para que aplique el cambio:
    ```bash
    sudo systemctl restart fundacionidear.service
    ```
¡Listo! Las nuevas solicitudes de Meta ahora serán reenviadas a tu bot de Telegram.

---

## 5. Ejemplos de Configuración para `config.json` del Reenviador

Para cambiar a qué bot se le envían los mensajes, solo necesitas editar `FORWARD_URL` y reiniciar `fundacionidear.service`.

**Ejemplo 1: Enviar a otro bot de WhatsApp en el puerto 5002**
```json
{
  "VERIFY_TOKEN": "fundacionidear2026",
  "FORWARD_URL": "http://127.0.0.1:5002/whatsapp"
}
```

**Ejemplo 2: Enviar a un bot de Telegram en el puerto 5003**
```json
{
  "VERIFY_TOKEN": "fundacionidear2026",
  "FORWARD_URL": "http://127.0.0.1:5003/telegram"
}
```

**Ejemplo 3: Enviar a un bot de Facebook Messenger en el puerto 5004**
```json
{
  "VERIFY_TOKEN": "fundacionidear2026",
  "FORWARD_URL": "http://127.0.0.1:5004/messenger"
}
```
