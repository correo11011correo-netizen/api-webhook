import os
import sys
from datetime import datetime

# --- Configurar Path para usar la lógica del Bot Engine Original ---
# Encontrar la ruta al bot-engine dentro del nuevo repositorio
# Suponiendo que este script corre en api-webhook/test-cli/bot-dashboard/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BOT_ENGINE_PATH = os.path.join(PROJECT_ROOT, 'bot-manager', 'bot-engine')

if BOT_ENGINE_PATH not in sys.path:
    sys.path.insert(0, BOT_ENGINE_PATH)

import db_manager
from engine import load_config, send_msg
from dotenv import load_dotenv

def clear_screen():
    """Limpia la terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_main_menu():
    """Muestra el menú principal."""
    clear_screen()
    print("=== Terminal Chat Manager (Conectado a Bot Engine) ===")
    print("1. Ver Chats")
    print("2. Salir")
    print("======================================================")

def get_conversations():
    """Obtiene todas las conversaciones de la base de datos central."""
    conn = db_manager.get_db_connection()
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
    conversations = cursor.fetchall()
    conn.close()
    return conversations

def display_conversations(conversations):
    clear_screen()
    print("=== Chats Activos ===")
    if not conversations:
        print("No hay conversaciones activas.")
        print("---------------------")
        return

    for i, conv in enumerate(conversations):
        status = "HUMANO" if conv['is_human_intervening'] else "BOT"
        last_msg = conv['last_message_content'] if conv['last_message_content'] else "No hay mensajes"
        name = conv['name'] if conv['name'] else conv['phone_number']
        print(f"{i+1}. {name} ({status}) - Último: '{last_msg}'")
    print("---------------------")

def get_messages_for_contact(phone_number):
    conn = db_manager.get_db_connection()
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
    messages = cursor.fetchall()
    conn.close()
    return messages

def display_chat_history(contact_info, messages):
    clear_screen()
    name = contact_info['name'] if contact_info['name'] else contact_info['phone_number']
    print(f"=== Chat con {name} ===")
    print(f"Estado de intervención: {'HUMANO' if contact_info['is_human_intervening'] else 'BOT'}")
    print("---------------------------------")
    for msg in messages:
        # Formateo de fecha
        try:
            timestamp = datetime.strptime(msg['timestamp'], '%Y-%m-%d %H:%M:%S.%f').strftime('%H:%M:%S')
        except ValueError:
            try:
                timestamp = datetime.strptime(msg['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')
            except ValueError:
                timestamp = msg['timestamp']
        
        sender_label = "Tú (Humano)" if msg['sender'] == 'human' else "Bot" if msg['sender'] == 'bot' else "Cliente"
        print(f"[{timestamp}] {sender_label}: {msg['content']}")
    print("---------------------------------")

def manage_chat(cfg, contact_info):
    while True:
        phone_number = contact_info['phone_number']
        messages = get_messages_for_contact(phone_number)
        
        # Leer estado actual
        is_intervening = db_manager.get_conversation_status(phone_number)
        contact_info['is_human_intervening'] = is_intervening

        display_chat_history(contact_info, messages)

        print("\nOpciones:")
        print("1. Responder mensaje")
        print("2. Cambiar estado de intervención (Pausar/Reanudar Bot)")
        print("3. Actualizar pantalla de Chat")
        print("4. Volver al menú principal")

        choice = input("Elige una opción: ")

        if choice == '1':
            message = input("Escribe tu mensaje: ")
            if message.strip():
                print("Enviando mensaje vía Meta API...")
                # Como el bot engine es agnóstico en la terminal, lo usamos
                # IMPORTANTE: engine.send_msg graba el mensaje como 'bot'. Lo pasaremos a 'human'.
                send_msg(cfg, phone_number, message)
                
                # Actualizar DB localmente para reflejar que fue un humano
                conn = db_manager.get_db_connection()
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
            db_manager.set_human_intervention_status(phone_number, new_status)
            input("Presiona Enter para continuar...")
            
        elif choice == '3':
            pass
            
        elif choice == '4':
            break
        else:
            print("Opción inválida.")
            input("Presiona Enter para continuar...")

def main():
    # Cargar .env de la carpeta correcta (bot-engine)
    env_path = os.path.join(BOT_ENGINE_PATH, '.env')
    load_dotenv(dotenv_path=env_path)
    
    # Cargar Configuración del bot engine
    cfg = load_config()

    while True:
        display_main_menu()
        choice = input("Elige una opción: ")

        if choice == '1':
            conversations = get_conversations()
            if not conversations:
                print("\nNo hay conversaciones activas. Presiona Enter para volver.")
                input()
                continue
            
            display_conversations(conversations)
            chat_choice = input("Elige el número del chat para gestionar (o 'q' para volver): ")
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
