# Documentación de Integración: Base de Datos de Chats (bot_dashboard.db) y Bot Engine

Esta documentación describe la estructura y el uso de la base de datos SQLite `bot_dashboard.db` utilizada por el administrador de bots, así como el funcionamiento del servicio principal (**Bot Engine**) que la gestiona. Su objetivo es facilitar la comprensión de la arquitectura actual y la integración de estos datos con otros servicios, APIs o paneles de control (dashboards).

---

## 1. Arquitectura del Servicio: Bot Engine (Motor del Bot)

El servicio principal que administra la base de datos es el **Bot Engine**. Es una aplicación web desarrollada en Python (utilizando Flask) que se ejecuta en el servidor (actualmente mediante Gunicorn).

Este servicio actúa como el "cerebro" central de la plataforma y realiza dos funciones críticas:

### 1.1. Manejo de Webhooks (Integración con Meta)
Es el puente de comunicación entre las APIs oficiales de Meta (WhatsApp, Instagram, Messenger) y la base de datos local.
*   **Recepción (`/api/webhook` - GET/POST):** Meta envía los eventos (nuevos mensajes) a esta ruta. El servicio valida los tokens de seguridad y procesa el JSON recibido.
*   **Procesamiento Lógico:** Evalúa el mensaje entrante contra los menús y flujos predefinidos para decidir si debe enviar una respuesta automática.
*   **Registro Automático:** Cada interacción (mensaje recibido del cliente o respuesta enviada por el bot) se registra instantáneamente en las tablas `contacts` y `messages` de la base de datos.

### 1.2. Gestión de la Intervención Humana (Activar/Desactivar Bot)
El Bot Engine tiene la capacidad de **pausar temporalmente** las respuestas automáticas para un usuario específico, permitiendo que un agente humano tome el control de la conversación.

*   **¿Cómo funciona?** El motor lee constantemente la tabla `conversations`. Si para un número de teléfono específico el campo `is_human_intervening` es `1` (True), el motor ignorará los mensajes entrantes de ese usuario y **no enviará respuestas automáticas**.
*   **Activación:** Un servicio externo (como el CLI, un Dashboard web o una API) puede cambiar este valor a `1` en la base de datos. Al hacerlo, el Bot Engine, en su siguiente lectura para ese usuario, detendrá sus respuestas.
*   **Reactivación:** Cuando el agente termina, se cambia `is_human_intervening` a `0`. El motor vuelve a tomar el control y responderá al siguiente mensaje del usuario.

---

## 2. Estructura de la Base de Datos (Esquema)

La base de datos es relacional y consta de tres tablas principales. El diseño está centrado en el contacto (usuario de WhatsApp/Instagram), sus conversaciones y el historial de mensajes.

### Tabla `contacts`
Almacena la información principal de los usuarios que interactúan con el bot.

*   `id` (INTEGER PRIMARY KEY AUTOINCREMENT): Identificador único interno del contacto.
*   `phone_number` (TEXT NOT NULL UNIQUE): Número de teléfono del contacto (generalmente con código de país, ej. `5493765245980`). Es el identificador principal para consultas externas.
*   `name` (TEXT): Nombre del contacto en caso de estar disponible (puede ser nulo o vacío).

### Tabla `conversations`
Maneja el estado global de la conversación con un contacto, vital para la función de intervención humana del Bot Engine.

*   `id` (INTEGER PRIMARY KEY AUTOINCREMENT): Identificador único.
*   `contact_id` (INTEGER NOT NULL UNIQUE): Clave foránea que referencia a `contacts(id)`.
*   `is_human_intervening` (BOOLEAN DEFAULT 0): Bandera fundamental leída por el Bot Engine. Si es `1`, el bot se silencia; si es `0`, el bot responde.
*   `last_updated` (DATETIME DEFAULT CURRENT_TIMESTAMP): Fecha y hora de la última actualización de estado.

### Tabla `messages`
Almacena el historial cronológico de todos los mensajes enviados y recibidos.

*   `id` (INTEGER PRIMARY KEY AUTOINCREMENT): Identificador único del mensaje.
*   `contact_id` (INTEGER NOT NULL): Clave foránea que referencia a `contacts(id)`.
*   `sender` (TEXT NOT NULL): Origen del mensaje. Valores posibles:
    *   `'client'`: Mensaje recibido del usuario final.
    *   `'bot'`: Mensaje enviado automáticamente por el Bot Engine.
    *   `'human'`: Mensaje enviado manualmente por un agente.
*   `message_type` (TEXT NOT NULL): Tipo de contenido (ej. `'text'`, `'image'`, `'button'`, `'audio'`, etc.).
*   `content` (TEXT NOT NULL): El cuerpo del mensaje (el texto en sí o la URL de la imagen/archivo).
*   `timestamp` (DATETIME DEFAULT CURRENT_TIMESTAMP): Fecha y hora exacta en que se registró el mensaje.

---

## 3. Ejemplos de Consultas SQL (Para uso en APIs/Servicios)

Aquí tienes ejemplos de cómo obtener la información más común para integrarla en endpoints de tu API o servicio backend (ej. usando Python, Node.js, PHP, etc.).

### A. Obtener la lista de chats activos (Último mensaje por usuario)
Ideal para una pantalla principal de un Dashboard.

```sql
SELECT
    c.phone_number,
    c.name,
    conv.is_human_intervening,
    MAX(m.timestamp) AS last_message_timestamp,
    (SELECT content FROM messages WHERE contact_id = c.id ORDER BY timestamp DESC LIMIT 1) AS last_message_content
FROM contacts c
LEFT JOIN conversations conv ON c.id = conv.contact_id
LEFT JOIN messages m ON c.id = m.contact_id
GROUP BY c.id
ORDER BY last_message_timestamp DESC;
```

### B. Obtener el historial completo de un chat específico
Ideal para mostrar la vista de mensajes cuando se selecciona un contacto. Reemplaza `?` por el número de teléfono.

```sql
SELECT
    m.sender,
    m.message_type,
    m.content,
    m.timestamp
FROM messages m
JOIN contacts c ON m.contact_id = c.id
WHERE c.phone_number = ?
ORDER BY m.timestamp ASC;
```

### C. Pausar el Bot para un usuario (Intervención Humana)
Esta consulta es la que permite a un sistema externo decirle al Bot Engine que deje de responder.

```sql
-- Primero, obtener el contact_id (o usar subconsultas)
-- Luego actualizar (o insertar) en conversations
INSERT INTO conversations (contact_id, is_human_intervening)
VALUES ((SELECT id FROM contacts WHERE phone_number = ?), 1)
ON CONFLICT(contact_id) DO UPDATE SET
is_human_intervening = 1,
last_updated = CURRENT_TIMESTAMP;
```

### D. Registrar un mensaje enviado por un Humano
Si tu API externa envía un mensaje vía Meta/WhatsApp usando sus credenciales, debes registrarlo en esta DB para que el historial que ve el cliente y el sistema sea consistente.

```sql
INSERT INTO messages (contact_id, sender, message_type, content)
VALUES (
    (SELECT id FROM contacts WHERE phone_number = ?),
    'human',
    'text',
    ? -- Aquí va el contenido del mensaje enviado
);
```

---

## 4. Guía de Integración y Posibles Usos

La arquitectura actual (Bot Engine independiente + Base de Datos local) permite expandir la plataforma de varias maneras.

### Opciones de Expansión
1.  **Dashboard Web (CRM):** Puedes crear un panel web moderno (React, Vue) que consuma una nueva API. Esta API simplemente leería y escribiría en `bot_dashboard.db` para mostrar chats, pausar bots (actualizando `is_human_intervening`) y enviar mensajes.
2.  **Integración con Servicios Externos:** Puedes crear un script que lea constantemente la tabla `messages` y reenvíe los mensajes nuevos a un CRM externo (como HubSpot o Salesforce).
3.  **App Móvil para Agentes:** Una app móvil podría conectarse a una API expuesta en tu servidor para notificar a los agentes en sus teléfonos cuando un cliente necesite intervención humana.

### Recomendaciones Técnicas
1.  **Ampliar el Bot Engine vs. API Separada:**
    *   *Opción A:* Puedes añadir nuevas rutas (ej. `@app.route('/api/external/chats')`) directamente en `server.py` del Bot Engine. Es más fácil de implementar inicialmente.
    *   *Opción B:* Puedes crear un servicio API completamente nuevo (ej. en Node.js o FastAPI) que corra en otro puerto y se conecte al mismo archivo SQLite. Es mejor para separar responsabilidades a largo plazo.
2.  **Manejo de Concurrencia (Bloqueos de SQLite):**
    Si decides ir por la *Opción B* (múltiples servicios accediendo a la DB), asegúrate de establecer un tiempo de espera (`timeout`) en las conexiones para evitar errores `database is locked`.
3.  **Directorio y Permisos:**
    En el servidor, la base se encuentra en: `/home/nestorfabianriveros2014/bot-manager/database/bot_dashboard.db`. Cualquier nuevo servicio debe ejecutarse con un usuario que tenga permisos de lectura/escritura en ese archivo y en la carpeta `/database` para que SQLite funcione correctamente.