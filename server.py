import socket
import threading
from server_utils import send_to_client, broadcast, get_client_list

HOST = '127.0.0.1'
PORT = 5000

clients = {}
client_counter = 0
clients_lock = threading.Lock()

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
                        send_to_client(clients, clients_lock, target_id, f"MSG:{client_id}:{content}")
                        print(f"[ROUTED] Client {client_id} → Client {target_id}")
                    except ValueError:
                        send_to_client(clients, clients_lock, client_id, "ERROR:Invalid client ID")

            elif message.startswith("BROADCAST:"):
                content = message.split(":", 1)[1]
                broadcast(clients, clients_lock, f"MSG:{client_id}:{content}", exclude_id=client_id)
                print(f"[BROADCAST] Client {client_id} to all")

            elif message == "LIST":
                client_list = get_client_list(clients, clients_lock)
                clients_str = ",".join(map(str, client_list))
                send_to_client(clients, clients_lock, client_id, f"CLIENTS:{clients_str}")
                print(f"[LIST] Sent to Client {client_id}: {clients_str}")

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

print(f"[SERVER STARTED] Listening on {HOST}:{PORT}")
print(f"[INFO] Waiting for client connections...")

try:
    while True:
        client_socket, address = server_socket.accept()

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
    server_socket.close()
