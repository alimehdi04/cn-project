import socket
import threading
import sys

class TCPClient:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        self.client_id = None
        
    def connect_to_server(self):
        """Connect to the server"""
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"✓ Connected to server at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to server: {e}")
            return False
    
    def receive_messages(self):
        """Continuously listen for messages from the server"""
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                
                if not message:
                    print("\n✗ Server disconnected")
                    self.running = False
                    break
                
                # Parse different message types from server
                if message.startswith("MSG:"):
                    # Format: MSG:sender_id:content
                    parts = message.split(":", 2)
                    if len(parts) == 3:
                        sender_id = parts[1]
                        content = parts[2]
                        print(f"\n[Client {sender_id} → You]: {content}")
                        print("You: ", end="", flush=True)
                        
                elif message.startswith("CLIENTS:"):
                    # Format: CLIENTS:1,2,3,4
                    client_list = message.split(":", 1)[1]
                    print(f"\n[Server]: Connected clients: {client_list}")
                    print("You: ", end="", flush=True)
                    
                elif message.startswith("ERROR:"):
                    # Format: ERROR:message
                    error_msg = message.split(":", 1)[1]
                    print(f"\n[Server Error]: {error_msg}")
                    print("You: ", end="", flush=True)
                    
                else:
                    # Unknown message format
                    print(f"\n[Server]: {message}")
                    print("You: ", end="", flush=True)
                    
            except ConnectionResetError:
                print("\n✗ Connection lost")
                self.running = False
                break
            except Exception as e:
                if self.running:
                    print(f"\n✗ Error receiving message: {e}")
                break
    
    def send_messages(self):
        """Take user input and send to server"""
        print("\n" + "="*60)
        print("COMMANDS:")
        print("  SEND:<client_id>:<message>    - Send to specific client")
        print("  BROADCAST:<message>            - Send to all clients")
        print("  LIST                           - Get list of connected clients")
        print("  quit/exit                      - Disconnect")
        print("="*60 + "\n")
        
        while self.running:
            try:
                message = input("You: ")
                
                if message.lower() in ['quit', 'exit']:
                    print("Disconnecting...")
                    self.running = False
                    break
                
                if message.strip():  # Only send non-empty messages
                    self.client_socket.send(message.encode('utf-8'))
                    
            except KeyboardInterrupt:
                print("\n\nDisconnecting...")
                self.running = False
                break
            except Exception as e:
                if self.running:
                    print(f"✗ Error sending message: {e}")
                break
    
    def start(self):
        """Start the client"""
        if not self.connect_to_server():
            return
        
        # Create threads for sending and receiving
        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        send_thread = threading.Thread(target=self.send_messages, daemon=True)
        
        # Start both threads
        receive_thread.start()
        send_thread.start()
        
        # Wait for send thread to finish (when user quits)
        send_thread.join()
        
        # Cleanup
        self.close()
    
    def close(self):
        """Close the connection"""
        try:
            self.running = False
            self.client_socket.close()
            print("✓ Disconnected from server")
        except:
            pass
        sys.exit(0)


def main():
    # Server configuration
    HOST = '127.0.0.1'  # Change to server IP if on different machine
    PORT = 5000         # Must match server port
    
    print("="*60)
    print("TCP CLIENT - Multi-Client Chat System")
    print("="*60)
    
    # Create and start client
    client = TCPClient(HOST, PORT)
    client.start()


if __name__ == "__main__":
    main()
