@echo off
title WhatsApp Hub - Local Test (Final Path & Env)
set LOG_DIR=logs
set SERVER_LOG=%LOG_DIR%\server.log

:: MOVERSE A LA CARPETA DEL SCRIPT
cd /d "%~dp0"

echo [%date% %time%] Iniciando Servidor de WhatsApp Hub...

if not exist %LOG_DIR% mkdir %LOG_DIR%

echo --------------------------------------------------
echo [1/2] Validando Dependencias...
echo [%date% %time%] Validando dependencias... >> %INSTALL_LOG%

:: Usar python -m pip para asegurar que instalamos en el python activo
python -m pip install Flask Flask-CORS python-dotenv psycopg2-binary requests >> %LOG_DIR%\install.log 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [+] Dependencias verificadas correctamente.
) else (
    echo [-] Error instalando dependencias. Revisa logs\install.log
    pause
    exit /b
)

echo --------------------------------------------------
echo [2/2] Lanzando dashboard_api.py...
powershell -Command "python dashboard_api.py | Tee-Object -FilePath '%SERVER_LOG%'"

echo --------------------------------------------------
echo [%date% %time%] Servidor detenido.
pause
