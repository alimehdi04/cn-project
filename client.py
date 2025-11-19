import socket
import threading
import sys
import signal

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
                    
            except (ConnectionResetError, BrokenPipeError, OSError):
                if self.running:
                    print("\n✗ Connection lost")
                    self.running = False
                break
            except Exception as e:
                if self.running:
                    print(f"\n✗ Error receiving message: {e}")
                    self.running = False
                break
    
    def send_messages(self):
        """Take user input and send to server"""
        print("\n" + "="*60)
        print("COMMANDS:")
        print("  SEND:<client_id>:<message>    - Send to specific client")
        print("  BROADCAST:<message>            - Send to all clients")
        print("  LIST                           - Get list of connected clients")
        print("  quit/exit                      - Disconnect")
        print("  Ctrl+C                         - Force disconnect")
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
                # Handle Ctrl+C gracefully
                print("\n\n[Interrupted] Disconnecting...")
                self.running = False
                break
            except (BrokenPipeError, OSError):
                # Connection already closed
                if self.running:
                    print("\n✗ Connection lost")
                    self.running = False
                break
            except EOFError:
                # Handle Ctrl+D (EOF)
                print("\n[EOF] Disconnecting...")
                self.running = False
                break
            except Exception as e:
                if self.running:
                    print(f"\n✗ Error sending message: {e}")
                    self.running = False
                break
    
    def start(self):
        """Start the client"""
        if not self.connect_to_server():
            return
        
        # Set up signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Create threads for sending and receiving
        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        send_thread = threading.Thread(target=self.send_messages)
        
        # Start both threads
        receive_thread.start()
        send_thread.start()
        
        # Wait for send thread to finish (when user quits)
        send_thread.join()
        
        # Cleanup
        self.close()
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C signal"""
        print("\n\n[Signal] Received interrupt signal. Shutting down...")
        self.running = False
        # Force exit after cleanup
        try:
            self.client_socket.close()
        except:
            pass
        sys.exit(0)
    
    def close(self):
        """Close the connection"""
        self.running = False
        try:
            # Shutdown socket to unblock any receive operations
            self.client_socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        
        try:
            self.client_socket.close()
            print("✓ Disconnected from server")
        except:
            pass


def main():
    # Server configuration
    HOST = '127.0.0.1'  # Change to server IP if on different machine
    PORT = 5000         # Must match server port
    
    print("="*60)
    print("TCP CLIENT - Multi-Client Chat System")
    print("="*60)
    
    try:
        # Create and start client
        client = TCPClient(HOST, PORT)
        client.start()
    except KeyboardInterrupt:
        print("\n\n[Interrupted] Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
