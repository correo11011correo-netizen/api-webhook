# API Webhook y Bot Engine

Este repositorio contiene el código de producción del webhook y del motor del bot de la Fundación IDEAR. Aquí están las instrucciones exactas de recuperación y despliegue del servicio desde cero en caso de necesitar reinstalar el sistema.

## Pasos para Desplegar

1. **Clonar el Repositorio**
   Clona el repositorio en tu servidor. El contenido de este repositorio debe ubicarse idealmente en los directorios de trabajo separados:
   - `api-fundacion-idear-webhook/`
   - `bot-manager/bot-engine/`

2. **Crear Entornos Virtuales e Instalar Dependencias**
   Para cada una de las dos carpetas (`api-fundacion-idear-webhook` y `bot-manager/bot-engine`), crea su propio entorno virtual e instala los requerimientos:
   ```bash
   # En api-fundacion-idear-webhook
   cd api-fundacion-idear-webhook
   python3 -m venv env
   source env/bin/activate
   pip install -r requirements.txt
   deactivate

   # En bot-manager/bot-engine
   cd ../bot-manager/bot-engine
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   deactivate
   ```

3. **Configurar Variables de Entorno**
   En la carpeta `bot-manager/bot-engine`, encontrarás un archivo llamado `.env.example`. Cópialo y renómbralo a `.env`:
   ```bash
   cp .env.example .env
   ```
   Edita el nuevo archivo `.env` añadiendo tus contraseñas y credenciales reales (Token de Meta, Puerto, Webhook Token, etc). **Nunca subas el archivo `.env` al repositorio.**

4. **Configurar Systemd (Demonios)**
   Para que los servicios corran en el fondo y se reinicien solos, copia los archivos `.service` proveídos:
   ```bash
   sudo cp api-fundacion-idear-webhook/deployment/fundacionidear.service /etc/systemd/system/
   sudo cp bot-manager/bot-engine/deployment/bot-engine.service /etc/systemd/system/
   ```
   Recarga los demonios e inicia los servicios:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable fundacionidear.service bot-engine.service
   sudo systemctl start fundacionidear.service bot-engine.service
   ```

5. **Configurar Apache (Proxy Reverso)**
   Configura tu servidor web (Apache o Nginx). Hay una plantilla de configuración provista en `api-fundacion-idear-webhook/deployment/apache-proxy.conf`.
   Asegúrate de agregar las reglas de `ProxyPass`:
   - `/webhook` a `http://127.0.0.1:5000/webhook` (El servicio Fundacion Idear)
   - `/dashboard` a `http://127.0.0.1:5001/dashboard` (El panel de Bot Engine)
   
   Reinicia Apache:
   ```bash
   sudo systemctl restart apache2
   ```

Con estos pasos, el servicio deberá quedar 100% operativo.
