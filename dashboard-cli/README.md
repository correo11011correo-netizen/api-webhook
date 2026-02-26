# Dashboard CLI Manager

Esta carpeta contiene la implementación del `cli_chat_manager.py` desacoplado del Bot Engine, utilizando conexión directa a la base de datos `bot_dashboard.db`. 

## Archivos en esta implementación:

1. **`cli_chat_manager.py`**: El script ejecutable. Puedes correrlo con `python3 cli_chat_manager.py`. Automáticamente buscará el `.env` en la carpeta `bot-engine` y se conectará a la base de datos en `bot-manager/database/bot_dashboard.db`.
2. **`SYSTEM_ARCHITECTURE.md`**: Documentación detallada sobre la arquitectura del sistema. Explica por qué el Bot Engine y este CLI están separados, y cómo el CLI asume el control ("is_human_intervening") pausando el bot asíncronamente.
3. **`DATABASE_INTEGRATION.md`**: Documentación con el esquema de la base de datos de chats y ejemplos de cómo realizar consultas SQL. Ideal para extender esta funcionalidad o llevarla a una interfaz web en el futuro.

## ¿Cómo ejecutar el Chat Manager?

Debes asegurarte de tener instaladas las dependencias (las mismas que el motor, principalmente `python-dotenv` y `requests`). 

Ejecútalo desde la terminal de tu servidor (o local si tienes acceso a los archivos):

```bash
python3 cli_chat_manager.py
```

Al hacerlo, podrás:
- Ver la lista de todos los chats activos y el último mensaje.
- Entrar a la conversación de un contacto en particular.
- Intervenir la conversación pausando el Bot automático.
- Enviar respuestas directamente desde tu terminal como "Humano".
