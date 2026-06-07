# Project Guidelines: Plataforma WhatsApp (Integrated with Stock Pro)

Este archivo es la fuente de verdad técnica para la Plataforma de WhatsApp. Todo desarrollo debe seguir estas directrices para mantener la consistencia con el ecosistema Stock Pro.

## ??? 1. Arquitectura de Datos Híbrida
El sistema opera con dos capas de persistencia para optimizar seguridad y rendimiento:

- **DB Global (PostgreSQL - Stock Pro):** 
  - **Propósito:** Gestión de Identidad y Acceso (IAM).
  - **Tablas Clave:** `users`, `tenants`, `sessions`.
  - **Responsabilidad:** Validar quién puede entrar al Hub y a qué tenant pertenece.
- **DB Local (SQLite - WhatsApp):** 
  - **Propósito:** Gestión de mensajería y estado del bot.
  - **Tablas Clave:** `contacts`, `messages`, `conversations`.
  - **Responsabilidad:** Almacenar el historial de chats y el estado de intervención humana.

## ?? 2. Modelo de Autenticación y Sesiones
La plataforma no gestiona usuarios propios; delega la confianza en Stock Pro.

- **Flujo de Login:** 
  1. El usuario ingresa credenciales $\rightarrow$ API de WhatsApp consulta la DB Global de Stock Pro.
  2. Si es válido, se genera un `token` (UUID) que se inserta en la tabla `sessions` de la DB Global.
- **Validación:** Cada petición a la API debe incluir el token en el header `Authorization`. El middleware `validate_session` verifica la existencia y expiración del token en Postgres.

## ?? 3. Interfaz de Usuario (Hub de Acceso)
El frontend está diseñado como un sistema de módulos accesibles desde un Hub Central.

- **Hub Maestro (`hub.html`):** Punto de entrada post-login. Distribuye el tráfico hacia los paneles específicos.
- **Panel de Chats (`index.html`):** Interfaz de mensajería en tiempo real.
- **Configuración (`settings.html`):** Gestión de API Keys de Meta y Webhooks.

## ?? 4. Despliegue y Entorno (Railway)
El sistema se despliega en Railway utilizando un entorno de Python (Flask).

- **Variables Críticas:**
  - `DATABASE_URL`: Conexión a la DB Global de Stock Pro (PostgreSQL).
  - `SECRET_KEY`: Clave para firmado de sesiones de Flask.
  - `META_TOKEN` / `PHONE_NUMBER_ID`: Credenciales de la API de WhatsApp Business.

## ??? 5. Estándares de Calidad y Debugging
- **Auditoría:** Se debe ejecutar `audit_whatsapp.py` tras cada despliegue en producción.
- **Logs:** Utilizar el módulo `logging` de Python con prefijos claros (`[WhatsAppAPI]`) para facilitar la trazabilidad en los logs de Railway.
- **Pruebas Rápidas:** Usar `test_api_wa.sh` para validar endpoints sin necesidad de frontend.
