# Diagnóstico Final: Error 404 con Gunicorn

## 1. Resumen del Problema

Tras resolver los problemas de proxy de Apache, el servidor backend se migró de `Flask Development Server` a `Gunicorn` para un entorno de producción más robusto.

El proxy inverso de Apache ahora funciona correctamente (confirmado por la cabecera `X-Apache-Config: active-ssl-conf` y la respuesta `Server: gunicorn`), pero el endpoint `/dashboard` **sigue devolviendo un 404 Not Found**. La diferencia crucial es que **este 404 ahora proviene de Gunicorn/Flask**, no de Apache.

Este directorio contiene la instantánea final de la configuración y los logs para diagnosticar por qué la aplicación Flask, servida por Gunicorn, no está encontrando la ruta `/dashboard`.

---

## 2. Análisis del Estado Final

- **Apache**: Funciona. Su rol de proxy inverso se está ejecutando correctamente. Reenvía las peticiones para `api.fundacionidear.com` al backend en `127.0.0.1:5000`.
- **Gunicorn**: Funciona. El servicio `systemd` (`final_fundacionidear.service`) lo ejecuta correctamente. Gunicorn recibe las peticiones reenviadas por Apache.
- **Flask (`app.py`)**: Aquí reside el problema. Aunque el código contiene la ruta `@app.route('/dashboard')`, Gunicorn no la está sirviendo.

**Posibles Causas del Error 404 de Gunicorn:**

1.  **Versión del Código Incorrecta**: Gunicorn podría estar ejecutando una versión en caché o antigua de `app.py` que no tiene la ruta `/dashboard`.
2.  **Error al Encontrar Plantillas**: La aplicación podría estar fallando al intentar renderizar `dashboard.html` porque Gunicorn (a diferencia del servidor de desarrollo de Flask) puede tener una ruta de trabajo (`working directory`) que no le permite encontrar la carpeta `templates/`.
3.  **Conflicto de Rutas o Blueprints**: Si la aplicación fuera más compleja, podría haber un conflicto de rutas.

---

## 3. Contenido de los Archivos de Diagnóstico

- **`app.py`**: El código fuente de la aplicación Flask que se supone que Gunicorn está ejecutando. Contiene la ruta `/dashboard`.

- **`final_fundacionidear.service`**: El archivo de servicio `systemd` final. **Punto clave**: `ExecStart=/usr/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app`. Muestra cómo se inicia Gunicorn.

- **`final_apache.conf`**: La configuración final y funcional del VirtualHost de Apache, usando `RewriteRule` para reenviar todo el tráfico al backend.

- **`latest_api_access.log`**: El log de acceso de Apache. Muestra las peticiones a `/dashboard` llegando y siendo procesadas, aunque finalmente resulten en un 404 del backend.

- **`gunicorn_service.log`**: **El log más importante para este diagnóstico.** Es la salida estándar y de error del proceso Gunicorn, capturada por `journalctl`. Cualquier error de Python, como "Template not found", aparecerá aquí.
