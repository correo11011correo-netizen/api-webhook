import requests 
import json
import uuid
import logging
from datetime import datetime

# --- CONFIGURACIÓN ---
# Cambiar por la URL de producción de Railway cuando se despliegue
BASE_URL = "http://localhost:5002" 
# Credenciales de prueba (deben existir en la DB Global de Stock Pro)
TEST_USER = "admin" 
TEST_PASS = "idear2024"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger("WhatsAppAudit") 

class WhatsAppAuditSuite:
    def __init__(self):
        self.token = None
        self.results = []

    def log_result(self, test_name, success, message=""):
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        self.results.append({"test": test_name, "status": status, "msg": message})
        logger.info(f"{status} | {test_name} {f'({message})' if message else ''}")

    def api_call(self, endpoint, method="POST", data=None, headers=None):
        if data is None: data = {}
        if headers is None: headers = {}

        if self.token:
            headers['Authorization'] = self.token 

        try:
            url = f"{BASE_URL}{endpoint}"
            if method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def run_all(self):
        logger.info(f"🚀 Iniciando Auditoría de Plataforma WhatsApp en {BASE_URL}")

        # 1. FLUJO DE AUTENTICACIÓN
        res = self.api_call('/api/login', data={"username": TEST_USER, "password": TEST_PASS})
        if res.get("success") == True and "token" in res:
            self.token = res["token"]
            self.log_result("Login Sincronizado (Stock Pro)", True)
        else:
            self.log_result("Login Sincronizado (Stock Pro)", False, res.get("message"))
            return # Detener si no hay acceso

        # 2. FLUJO DE CHATS
        res = self.api_call('/api/chats', method="GET")
        if isinstance(res, list):
            self.log_result("Obtención de Lista de Chats", True, f"Encontrados {len(res)} chats")
        else:
            self.log_result("Obtención de Lista de Chats", False, str(res))

        # 3. FLUJO DE MENSAJES (Si hay al menos un chat)
        if isinstance(res, list) and len(res) > 0:
            phone = res[0]['phone_number']
            
            # Obtener mensajes
            msg_res = self.api_call(f'/api/chats/{phone}/messages', method="GET")
            self.log_result(f"Lectura de Mensajes ({phone})", isinstance(msg_res, dict) and "messages" in msg_res)

            # Probar Toggle de Intervención
            toggle_res = self.api_call(f'/api/chats/{phone}/toggle', data={"is_human_intervening": True})
            self.log_result(f"Cambio a Modo Humano ({phone})", toggle_res.get("success") == True)
        else:
            self.log_result("Flujo de Mensajes", False, "No hay chats disponibles para probar")

        # 4. SEGURIDAD
        # Intento de acceso sin token
        res_no_token = self.api_call('/api/chats', method="GET", headers={"Authorization": "token-invalido"})
        if res_no_token.get("message") == "Sesión no válida o expirada":
            self.log_result("Seguridad: Bloqueo de Token Inválido", True)
        else:
            self.log_result("Seguridad: Bloqueo de Token Inválido", False, str(res_no_token))

        # Resumen Final 
        print("
" + "="*50)
        print(f"RESUMEN DE AUDITORÍA WHATSAPP - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*50)
        passed = sum(1 for r in self.results if r["status"] == "✅ PASÓ")
        total = len(self.results)
        for r in self.results:
            print(f"{r['status']} | {r['test']}: {r['msg']}")
        print("="*50)
        print(f"RESULTADO FINAL: {passed}/{total} pruebas pasaron.")
        print("="*50)

if __name__ == "__main__":
    suite = WhatsAppAuditSuite()
    suite.run_all()
