# Arquitectura del Sistema: Bot Engine, Base de Datos y CLI Manager

Este documento explica de forma detallada la arquitectura del sistema de bots, cómo interactúan sus componentes (sin depender directamente el uno del otro) y cómo puedes replicar este modelo robusto en futuros proyectos.

El sistema está compuesto por tres pilares principales:
1. **Bot Engine (El Motor Central)**
2. **Base de Datos (bot_dashboard.db)**
3. **CLI Chat Manager (Interfaz de Agente Humano)**

---

## 1. El Motor Central (Bot Engine)
El Bot Engine (escrito en Python con Flask) es el cerebro que está expuesto a internet y maneja la automatización pura.

### Sus responsabilidades:
- **Recepción de Webhooks:** Escucha constantemente peticiones en la ruta `/api/webhook`. Cuando un cliente escribe a WhatsApp o Instagram, Meta envía el JSON con el mensaje a esta ruta.
- **Procesamiento de Reglas:** Evalúa el mensaje entrante y decide la respuesta automática basándose en los flujos predefinidos.
- **Escritor Principal:** Registra a los contactos nuevos y guarda absolutamente cada mensaje entrante (`sender: 'client'`) y saliente (`sender: 'bot'`) en la base de datos.

### El Secreto de la Intervención:
Antes de responder automáticamente, el Bot Engine hace una consulta rápida a la tabla `conversations` para revisar el campo `is_human_intervening`.
*   Si es `0`: El bot procesa su lógica y responde.
*   Si es `1`: El bot registra el mensaje del cliente en el historial, pero **aborta el proceso de respuesta**, permitiendo que un humano tome el control.

---

## 2. La Base de Datos (SQLite)
Es el único punto de la verdad (`bot_dashboard.db`). Funciona como el "puente de comunicación" entre el bot automático y las interfaces humanas.

### Tablas Clave:
- **`contacts`**: Los usuarios finales (sus números de teléfono).
- **`conversations`**: Maneja el estado global del chat. Contiene la bandera fundamental `is_human_intervening`.
- **`messages`**: El historial cronológico. Utiliza el campo `sender` para clasificar quién habló:
    - `'client'`: El cliente.
    - `'bot'`: El sistema automático.
    - `'human'`: Un agente real.

### ¿Por qué esta arquitectura es poderosa?
El Bot Engine y el CLI Manager **no se comunican directamente entre sí**. Se comunican modificando y leyendo la base de datos. Esto significa que puedes apagar el CLI, crear una app web nueva, o reiniciar servidores, y el estado de las conversaciones se mantiene intacto y sincronizado.

---

## 3. CLI Chat Manager (El Controlador Humano)
El script `cli_chat_manager.py` es un cliente independiente que demuestra cómo un sistema externo (o un agente humano) puede conectarse y tomar el control del ecosistema.

### Cómo funciona su código:
1. **Conexión Directa:** No utiliza APIs intermedias. Se conecta directamente al archivo SQLite usando la librería estándar de Python (`sqlite3`).
2. **Lectura en Vivo:** Realiza consultas SQL (`JOIN` entre `contacts`, `conversations` y `messages`) para listar los chats activos y mostrar los historiales en pantalla.
3. **Pausar el Bot (Tomar el Control):** Cuando el agente decide intervenir, el CLI hace un `UPDATE` en la tabla `conversations`, poniendo `is_human_intervening = 1`. 
   *   *Magia:* Automáticamente, el Bot Engine leerá este estado en el próximo mensaje del cliente y se quedará en silencio.
4. **Enviar Mensajes como Humano:**
   *   El CLI importa la función `send_msg` del Bot Engine porque esta contiene la lógica para conectarse a la API de Meta y enviar el mensaje real por WhatsApp.
   *   *Corrección de Identidad:* Dado que el motor asume que cualquier mensaje enviado por él es del bot, el CLI hace un pequeño truco: inmediatamente después de enviar el mensaje, hace un `UPDATE` en la tabla `messages` cambiando la etiqueta de ese último registro de `sender='bot'` a `sender='human'`. Así el historial queda perfecto.

---

## 4. Guía para Futuros Proyectos (Ej. Nuevo Dashboard Web)

Si en el futuro quieres crear un panel web moderno (por ejemplo, con React y Node.js) para reemplazar la terminal de comandos, sigue estas reglas basadas en esta arquitectura:

1. **Separa las Responsabilidades:**
   - Deja el Bot Engine (Python) intacto. Que siga recibiendo los webhooks de Meta y aplicando su lógica automática.
   - Tu nuevo Dashboard Web solo debe preocuparse por leer y escribir en la base de datos SQLite compartida.
2. **Usa la Base de Datos como API de Estado:**
   - Para silenciar al bot, tu Dashboard simplemente debe ejecutar la consulta: `UPDATE conversations SET is_human_intervening = 1 WHERE contact_id = X`. El Bot Engine lo acatará al instante.
3. **Para enviar mensajes desde el nuevo Dashboard:**
   - Tu backend de Node.js (o PHP/FastAPI) deberá hacer una petición HTTP POST directa a la API Graph de Meta (usando el Token de WhatsApp) para enviar el mensaje al cliente.
   - Inmediatamente después, debe ejecutar un `INSERT INTO messages` en la base de datos con `sender = 'human'` para que el historial se actualice.
4. **Manejo de Concurrencia (Bloqueos):**
   - Dado que SQLite bloquea el archivo momentáneamente al escribir, asegúrate de configurar tu conexión de base de datos en el nuevo proyecto con un `timeout` (tiempo de espera) prudencial (ej. 10 segundos). Si el proyecto crece a un nivel empresarial, simplemente migra estas 3 tablas de SQLite a PostgreSQL o MySQL, y la arquitectura completa seguirá funcionando exactamente igual.