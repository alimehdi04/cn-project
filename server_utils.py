def send_to_client(clients, clients_lock, client_id, message):
    with clients_lock:
        if client_id in clients:
            try:
                clients[client_id].send(message.encode('utf-8'))
                return True
            except Exception as e:
                print(f"[ERROR] Failed to send to Client {client_id}: {e}")
                return False
        else:
            print(f"[ERROR] Client {client_id} not found")
            return False

def broadcast(clients, clients_lock, message, exclude_id=None):
    with clients_lock:
        for cid, sock in clients.items():
            if cid != exclude_id:
                try:
                    sock.send(message.encode('utf-8'))
                except Exception as e:
                    print(f"[ERROR] Broadcast to Client {cid} failed: {e}")

def get_client_list(clients, clients_lock):
    with clients_lock:
        return list(clients.keys())
