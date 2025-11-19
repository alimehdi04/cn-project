import socket
import threading
from server_utils import send_to_client, broadcast, get_client_list
from message_manager import MessageManager

HOST = '127.0.0.1'
PORT = 5000

clients = {}
client_counter = 0
clients_lock = threading.Lock()


message_manager = MessageManager(auto_delete_interval=10, message_ttl=120)

def handle_client(client_socket, client_id):
    print(f"[THREAD STARTED] Handler for Client {client_id}")

    try:
        while True:
            data = client_socket.recv(1024)

            if not data:
                break

            message = data.decode('utf-8').strip()
            print(f"[CLIENT {client_id}] {message}")

            if message.startswith("SEND:"):
                parts = message.split(":", 2)
                if len(parts) == 3:
                    try:
                        target_id = int(parts[1])
                        content = parts[2]
                      
                        msg_id = message_manager.store_message(client_id, target_id, content)
                        send_to_client(clients, clients_lock, target_id, f"MSG:{client_id}:{content}")
                        send_to_client(clients, clients_lock, client_id, f"SENT:Message stored (ID:{msg_id})")
                        print(f"[ROUTED] Client {client_id} → Client {target_id} (MsgID:{msg_id})")
                    except ValueError:
                        send_to_client(clients, clients_lock, client_id, "ERROR:Invalid client ID")

            elif message.startswith("BROADCAST:"):
                content = message.split(":", 1)[1]
                
                client_list = get_client_list(clients, clients_lock)
                for target_id in client_list:
                    if target_id != client_id:
                        message_manager.store_message(client_id, target_id, content)
                broadcast(clients, clients_lock, f"MSG:{client_id}:{content}", exclude_id=client_id)
                print(f"[BROADCAST] Client {client_id} to all")
            elif message.lower() in ["quit", "exit", "disconnect"]:
                break
            elif message == "LIST":
                client_list = get_client_list(clients, clients_lock)
                clients_str = ",".join(map(str, client_list))
                send_to_client(clients, clients_lock, client_id, f"CLIENTS:{clients_str}")
                print(f"[LIST] Sent to Client {client_id}: {clients_str}")

            elif message.startswith("DELETE_MSG:"):
               
                try:
                    msg_id = int(message.split(":", 1)[1])
                    if message_manager.delete_message(msg_id):
                        send_to_client(clients, clients_lock, client_id, f"SUCCESS:Message {msg_id} deleted")
                    else:
                        send_to_client(clients, clients_lock, client_id, f"ERROR:Message {msg_id} not found")
                except ValueError:
                    send_to_client(clients, clients_lock, client_id, "ERROR:Invalid message ID")

            elif message.startswith("DELETE_CLIENT:"):
               
                try:
                    target_id = int(message.split(":", 1)[1])
                    count = message_manager.delete_client_messages(target_id)
                    send_to_client(clients, clients_lock, client_id, f"SUCCESS:Deleted {count} messages for Client {target_id}")
                except ValueError:
                    send_to_client(clients, clients_lock, client_id, "ERROR:Invalid client ID")

            elif message == "DELETE_ALL":
                # Clear entire message storage
                count = message_manager.clear_all_messages()
                send_to_client(clients, clients_lock, client_id, f"SUCCESS:Cleared {count} messages")

            elif message == "MSG_STATS":
                # Get message storage statistics
                stats = message_manager.get_stats()
                stats_str = f"STATS:Total={stats['total_messages']},Clients={stats['total_clients_with_messages']},TTL={stats['message_ttl_seconds']}s"
                send_to_client(clients, clients_lock, client_id, stats_str)

            elif message == "MSG_LIST":
                # List all messages for this client
                messages = message_manager.get_client_messages(client_id)
                if messages:
                    msg_list = []
                    for msg in messages:
                        direction = "sent" if msg.sender_id == client_id else "received"
                        other_id = msg.recipient_id if msg.sender_id == client_id else msg.sender_id
                        msg_list.append(f"ID:{msg.message_id},{direction},Client:{other_id}")
                    send_to_client(clients, clients_lock, client_id, f"MESSAGES:{';'.join(msg_list)}")
                else:
                    send_to_client(clients, clients_lock, client_id, "MESSAGES:No messages found")

            else:
                send_to_client(clients, clients_lock, client_id, "ERROR:Unknown command")

    except Exception as e:
        print(f"[ERROR] Client {client_id}: {e}")

    finally:
        with clients_lock:
            if client_id in clients:
                del clients[client_id]

        client_socket.close()
        print(f"[DISCONNECTED] Client {client_id} | Remaining clients: {len(clients)}")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)

server_socket.settimeout(1.0)

print(f"[SERVER STARTED] Listening on {HOST}:{PORT}")
print(f"[INFO] Waiting for client connections...")

try:
    while True:
        try :
            client_socket, address = server_socket.accept()

        except socket.timeout:
            
            continue

        with clients_lock:
            client_counter += 1
            client_id = client_counter
            clients[client_id] = client_socket

        print(f"[NEW CONNECTION] Client {client_id} connected from {address[0]}:{address[1]}")
        print(f"[INFO] Total clients connected: {len(clients)}")

        thread = threading.Thread(target=handle_client, args=(client_socket, client_id))
        thread.start()

except KeyboardInterrupt:
    print("\n[SERVER] Shutting down...")
    message_manager.stop()
    server_socket.close()