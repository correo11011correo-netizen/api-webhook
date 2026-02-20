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