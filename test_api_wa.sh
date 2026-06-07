#!/bin/bash

# Helper script para interactuar con la API de la Plataforma de WhatsApp via curl
# Permite depurar el backend sin necesidad de cargar el navegador.

API_URL="http://localhost:5002/api"

# Colores para la salida
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Herramienta de Pruebas de API - WhatsApp Hub ===${NC}"
echo -e "Servidor: $API_URL\n"

# Variable para guardar el token de sesión
TOKEN=""

# Función para ejecutar peticiones
execute_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    echo -e "${BLUE}Ejecutando: ${NC}$method $endpoint"
    if [ ! -z "$data" ]; then echo -e "Data: $data"; fi

    curl -s -X $method "$API_URL$endpoint" \
        -H "Content-Type: application/json" \
        -H "Authorization: $TOKEN" \
        -d "$data" | jq .
    echo -e "\n--------------------------------------------------\n"
}

# 1. Login (Obligatorio para obtener TOKEN)
echo -e "${GREEN}[1/4] Autenticando con Stock-Pro...${NC}"
read -p "Usuario: " user
read -p "Contraseña: " pass

LOGIN_RES=$(curl -s -X POST "$API_URL/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$user\", \"password\": \"$pass\"}")

TOKEN=$(echo $LOGIN_RES | jq -r '.token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo -e "${RED}Error: No se pudo obtener el token de sesión.${NC}"
    echo $LOGIN_RES
    exit 1
fi

echo -e "${GREEN}Token obtenido exitosamente: ${NC}$TOKEN\n"

# 2. Listar Chats
echo -e "${GREEN}[2/4] Probando /chats...${NC}"
execute_call "GET" "/chats"

# 3. Cambiar modo de intervención (Ejemplo con el primer teléfono)
echo -e "${GREEN}[3/4] Probando toggle de intervención...${NC}"
read -p "Teléfono para probar: " phone
execute_call "POST" "/chats/$phone/toggle" "{\"is_human_intervening\": true}"

# 4. Enviar Mensaje
echo -e "${GREEN}[4/4] Probando envío de mensaje...${NC}"
read -p "Mensaje: " msg
execute_call "POST" "/chats/$phone/send" "{\"message\": \"$msg\"}"

echo -e "${BLUE}=== Pruebas Completadas ===${NC}"
