import os
import sys
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# --- Rutas relativas al motor y a la base de datos central ---
# Este script asume que está en api-webhook/dashboard-cli/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Resolvemos las rutas hacia el bot-engine y la base de datos
# asumiendo que están en la carpeta bot-manager del repositorio
BOT_ENGINE_PATH = os.path.join(PROJECT_ROOT, 'bot-manager', 'bot-engine')
DB_PATH = os.path.join(PROJECT_ROOT, 'bot-manager', 'database', 'bot_dashboard.db')

if BOT_ENGINE_PATH not in sys.path:
    sys.path.insert(0, BOT_ENGINE_PATH)

# Importamos la configuración y función de envío del motor
try:
    from engine import load_config, send_msg
except ImportError:
    print("❌ Error: No se pudo importar 'engine.py'.")
    print(f"Verifica que el archivo exista en: {BOT_ENGINE_PATH}")
    sys.exit(1)

def get_db_connection():
    """Establece conexión directa con la base de datos central."""
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: No se encontró la base de datos en {DB_PATH}.")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_main_menu():
    clear_screen()
    print("=== Terminal Chat Manager (Conexión Directa a DB) ===")
    print("1. Ver Chats Activos")
    print("2. Salir")
    print("=====================================================")

def get_conversations():
    """Obtiene todas las conversaciones escaneando la base de datos central."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT
            c.id AS contact_id,
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
    """
    cursor.execute(query)
    conversations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return conversations

def display_conversations(conversations):
    clear_screen()
    print("=== Chats Activos (desde bot_dashboard.db) ===")
    if not conversations:
        print("No hay conversaciones activas.")
        print("---------------------")
        return

    for i, conv in enumerate(conversations):
        status = "HUMANO" if conv['is_human_intervening'] else "BOT"
        last_msg = conv['last_message_content'] if conv['last_message_content'] else "Sin mensajes"
        name = conv['name'] if conv['name'] else conv['phone_number']
        print(f"{i+1}. {name} ({status}) - Último: '{last_msg[:40]}'")
    print("---------------------")

def get_messages_for_contact(phone_number):
    """Lee el historial completo de mensajes directamente desde la DB"""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT
            m.sender,
            m.content,
            m.timestamp
        FROM messages m
        JOIN contacts c ON m.contact_id = c.id
        WHERE c.phone_number = ?
        ORDER BY m.timestamp ASC;
    """
    cursor.execute(query, (phone_number,))
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages

def get_conversation_status(phone_number):
    """Obtiene el estado de intervención leyendo la tabla conversations."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT conv.is_human_intervening 
        FROM conversations conv
        JOIN contacts c ON conv.contact_id = c.id
        WHERE c.phone_number = ?
    """, (phone_number,))
    row = cursor.fetchone()
    conn.close()
    return bool(row['is_human_intervening']) if row else False

def set_human_intervention_status(phone_number, status):
    """Actualiza el estado de intervención en la base de datos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversations (contact_id, is_human_intervening)
        VALUES ((SELECT id FROM contacts WHERE phone_number = ?), ?)
        ON CONFLICT(contact_id) DO UPDATE SET
        is_human_intervening = excluded.is_human_intervening,
        last_updated = CURRENT_TIMESTAMP;
    """, (phone_number, 1 if status else 0))
    conn.commit()
    conn.close()

def display_chat_history(contact_info, messages):
    clear_screen()
    name = contact_info['name'] if contact_info['name'] else contact_info['phone_number']
    print(f"=== Chat con {name} ===")
    print(f"Estado actual: {'HUMANO (Bot pausado)' if contact_info['is_human_intervening'] else 'BOT (Activo)'}")
    print("---------------------------------")
    for msg in messages:
        timestamp = msg['timestamp']
        if '.' in timestamp:
            timestamp = timestamp.split('.')[0]
        try:
            timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')
        except ValueError:
            pass
        
        sender_label = "Tú (Humano)" if msg['sender'] == 'human' else "Bot" if msg['sender'] == 'bot' else "Cliente"
        print(f"[{timestamp}] {sender_label}: {msg['content']}")
    print("---------------------------------")

def manage_chat(cfg, contact_info):
    while True:
        phone_number = contact_info['phone_number']
        messages = get_messages_for_contact(phone_number)
        
        # Refrescar estado actual directamente de DB
        is_intervening = get_conversation_status(phone_number)
        contact_info['is_human_intervening'] = is_intervening

        display_chat_history(contact_info, messages)

        print("
Opciones:")
        print("1. Responder mensaje")
        print("2. Cambiar estado de intervención (Pausar/Reanudar Bot)")
        print("3. Actualizar pantalla de Chat")
        print("4. Volver al menú principal")

        choice = input("Elige una opción: ")

        if choice == '1':
            message = input("Escribe tu mensaje: ")
            if message.strip():
                print("Enviando mensaje vía Meta API...")
                # send_msg lo registra internamente en DB como 'bot' 
                send_msg(cfg, phone_number, message)
                
                # Nosotros actualizamos directamente la DB para que figure como 'human'
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE messages 
                    SET sender = 'human' 
                    WHERE contact_id = (SELECT id FROM contacts WHERE phone_number = ?) 
                    AND sender = 'bot' 
                    ORDER BY timestamp DESC LIMIT 1
                """, (phone_number,))
                conn.commit()
                conn.close()
                print("✅ Mensaje enviado exitosamente.")
            input("Presiona Enter para continuar...")
            
        elif choice == '2':
            new_status = not is_intervening
            set_human_intervention_status(phone_number, new_status)
            print(f"✅ Estado actualizado a: {'HUMANO (Pausado)' if new_status else 'BOT (Activo)'}")
            input("Presiona Enter para continuar...")
            
        elif choice == '3':
            pass
            
        elif choice == '4':
            break
        else:
            print("Opción inválida.")
            input("Presiona Enter para continuar...")

def main():
    # Cargar el archivo .env desde el motor
    env_path = os.path.join(BOT_ENGINE_PATH, '.env')
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
    else:
        print(f"⚠️  Advertencia: No se encontró .env en {env_path}. Si las variables no están en el entorno, el bot fallará al enviar mensajes.")
    
    cfg = load_config()

    while True:
        display_main_menu()
        choice = input("Elige una opción: ")

        if choice == '1':
            conversations = get_conversations()
            if not conversations:
                print("
No hay conversaciones activas en la base de datos.")
                input("Presiona Enter para volver.")
                continue
            
            display_conversations(conversations)
            chat_choice = input("Elige el número del chat (o 'q' para volver): ")
            if chat_choice.lower() == 'q':
                continue
            
            try:
                chat_index = int(chat_choice) - 1
                if 0 <= chat_index < len(conversations):
                    manage_chat(cfg, dict(conversations[chat_index]))
                else:
                    print("Número de chat inválido.")
                    input("Presiona Enter para continuar...")
            except ValueError:
                print("Entrada inválida.")
                input("Presiona Enter para continuar...")

        elif choice == '2':
            sys.exit("Saliendo del Chat Manager.")
        else:
            print("Opción inválida.")
            input("Presiona Enter para continuar...")

if __name__ == '__main__':
    main()
