# Computer Networks Lab Assignment – 5th Semester

This repo contains the code for our Computer Networks lab assignment for the 5th semester.

## Task Description
We were tasked with writing a socket program to implement a TCP client and server such that:

- In a multi-client setup, there are **4 systems**, and each system should have **4 clients**.
- All clients can send data to the server.
- The server can send a message to any selected client.
- The user should be able to set a **timer** for deleting the message either after **2 minutes** or manually from the server.

## Implementation
The implementation has been done in **Python**, using socket programming to handle the multi-client communication and message-handling logic.

## Team Members
- Ayan Alam
- Ali Mehdi Naqvi
- Syed Abdul Saboor
- Saad Ahmed Siddiqui

---

## Code Explanation

### Server (server.py)

- Creates a TCP socket bound to 127.0.0.1:5000 using `socket.socket(AF_INET, SOCK_STREAM)`
- Uses `listen()` to accept multiple incoming connections
- Spawns a dedicated thread per client using `threading.Thread` for concurrent handling
- Maintains a `clients{}` dictionary mapping client_id to socket objects, protected by `threading.Lock` for thread-safe access
- Parses incoming commands (`SEND`, `BROADCAST`, `DELETE_MSG`, etc.) and routes messages accordingly
- Calls `MessageManager` methods to store/delete messages
- Uses `send_to_client()` for unicast and `broadcast()` for multicast message delivery

---

### Client (client.py)

- **Connection Establishment**
  - Creates a TCP socket using `socket.socket(AF_INET, SOCK_STREAM)`
  - Calls `connect((host, port))` to establish a TCP handshake with the server

- **Dual-Threaded Architecture**

  - **Receive Thread (`receive_messages()`):**
    - Runs in infinite loop calling `client_socket.recv(1024)` to read up to 1024 bytes
    - Decodes received bytes with UTF-8 and parses protocol-specific formats using `startswith()`
    - Handles different message types:
      - `MSG:` (incoming message)
      - `CLIENTS:` (list of online clients)
      - `SENT:` (send confirmation)
      - `SUCCESS:` (successful operation)
      - `ERROR:` (error message)
      - `STATS:` (server statistics)
      - `MESSAGES:` (list of stored messages)
    - Displays parsed messages with formatting
    - Prints prompt `"You: "` after each message for CLI consistency

  - **Send Thread (`send_messages()`):**
    - Blocks on `input("You: ")` waiting for user input
    - Encodes commands to UTF-8 and sends via `client_socket.send()`
    - Handles commands like `quit` / `exit` for graceful shutdown
    - Validates non-empty user input before sending

- **Concurrency Benefits**
  - Both threads run simultaneously, allowing asynchronous I/O (user can type while receiving)

- **Daemon Threads**
  - Threads created with `daemon=True` so they auto-terminate when main thread exits

- **Thread Synchronization**
  - `send_thread.join()` ensures main thread waits for user to finish before cleanup

---

### Message Manager (message_manager.py)

- **Dual-Index Storage Architecture**
  - `messages`: main storage mapping message_id → Message (O(1) lookup)
  - `client_messages`: maps client_id → list of message_ids (O(1) access to client history)
  - When storing a message, both sender and recipient are indexed for fast retrieval

- **Auto-Deletion Thread**
  - Created as daemon thread inside `__init__()`
  - Runs `_auto_delete_worker()` which:
    - Sleeps for 10 seconds using `time.sleep()`
    - Calls `_auto_delete_expired()` to find and remove expired messages
  - Expiration uses:
    ```python
    datetime.now() - self.timestamp > timedelta(seconds=ttl)
    ```
  - Expired messages are removed from both `messages` and `client_messages`

- **Thread Safety**
  - A single `threading.Lock()` ensures mutual exclusion for all shared data
  - `with self.lock:` guarantees proper acquisition and release, even on exceptions
  - Prevents race conditions between client threads and auto-delete thread
  - Lock is applied per operation to avoid deadlocks

- **Message Class**
  - Stores:
    - `sender_id` (int)
    - `recipient_id` (int)
    - `content` (string)
    - `message_id` (unique ID)
    - `timestamp` (creation time)
  - Used as a simple data transfer object encapsulating message metadata

---

## How to Run

### 1. Start the Server
```bash
python server.py
```

### 2. Start Clients (16 clients for 4 systems)
Open 16 separate terminals and run in each:
```bash
python client.py
```

### 3. Available Commands

**Send message to specific client:**
```
SEND:2:Hello Client 2!
```

**Send message to all clients:**
```
BROADCAST:Hello everyone!
```

**List connected clients:**
```
LIST
```

**View your messages:**
```
MSG_LIST
```

**Delete specific message:**
```
DELETE_MSG:1
```

**Delete all messages for a client:**
```
DELETE_CLIENT:2
```

**Clear all messages:**
```
DELETE_ALL
```

**View statistics:**
```
MSG_STATS
```

**Disconnect:**
```
quit
```

**Note:** Messages automatically delete after 2 minutes.