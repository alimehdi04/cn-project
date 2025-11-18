import threading
import time
from datetime import datetime, timedelta


class Message:
    """Represents a single message with metadata"""

    def __init__(self, sender_id, recipient_id, content, message_id):
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.content = content
        self.message_id = message_id
        self.timestamp = datetime.now()

    def is_expired(self, ttl_seconds=120):
        """Check if message has expired (default 2 minutes)"""
        return datetime.now() - self.timestamp > timedelta(seconds=ttl_seconds)

    def __repr__(self):
        return f"Message(id={self.message_id}, from={self.sender_id}, to={self.recipient_id}, time={self.timestamp})"


class MessageManager:
    """
    Manages message storage with auto-deletion and manual deletion controls.

    Features:
    - Stores messages with timestamps
    - Auto-deletes messages older than 2 minutes (background thread runs every 10 seconds)
    - Manual deletion options:
        - Delete all messages for a specific client
        - Delete a specific message by ID
        - Clear entire message storage
    """

    def __init__(self, auto_delete_interval=10, message_ttl=120):
        """
        Initialize message manager.

        Args:
            auto_delete_interval: Seconds between auto-delete checks
            message_ttl: Time-to-live for messages in seconds
        """
        self.messages = {}  # message_id -> Message
        self.client_messages = {}  # client_id -> [message_ids]
        self.message_counter = 0
        self.lock = threading.Lock()

        self.auto_delete_interval = auto_delete_interval
        self.message_ttl = message_ttl
        self.running = True

        # Start background auto-delete thread
        self.auto_delete_thread = threading.Thread(target=self._auto_delete_worker, daemon=True)
        self.auto_delete_thread.start()
        print(f"[MESSAGE MANAGER] Started (auto-delete every {auto_delete_interval}s, TTL: {message_ttl}s)")

    def store_message(self, sender_id, recipient_id, content):
        """
        Store a new message.
        """
        with self.lock:
            self.message_counter += 1
            message_id = self.message_counter

            msg = Message(sender_id, recipient_id, content, message_id)
            self.messages[message_id] = msg

            if sender_id not in self.client_messages:
                self.client_messages[sender_id] = []
            self.client_messages[sender_id].append(message_id)

            if recipient_id not in self.client_messages:
                self.client_messages[recipient_id] = []
            self.client_messages[recipient_id].append(message_id)

            print(f"[MESSAGE STORED] ID={message_id}, From={sender_id}, To={recipient_id}")
            return message_id

    def get_message(self, message_id):
        """Get a message by ID"""
        with self.lock:
            return self.messages.get(message_id)

    def get_client_messages(self, client_id):
        """Get all messages associated with a client (sent or received)"""
        with self.lock:
            if client_id not in self.client_messages:
                return []

            msg_ids = self.client_messages[client_id]
            return [self.messages[mid] for mid in msg_ids if mid in self.messages]

    def get_all_messages(self):
        """Get all stored messages"""
        with self.lock:
            return list(self.messages.values())

    def delete_message(self, message_id):
        """
        Delete a specific message by ID.
        """
        with self.lock:
            if message_id not in self.messages:
                return False

            msg = self.messages[message_id]

            if msg.sender_id in self.client_messages:
                if message_id in self.client_messages[msg.sender_id]:
                    self.client_messages[msg.sender_id].remove(message_id)

            if msg.recipient_id in self.client_messages:
                if message_id in self.client_messages[msg.recipient_id]:
                    self.client_messages[msg.recipient_id].remove(message_id)

            del self.messages[message_id]
            print(f"[MESSAGE DELETED] ID={message_id}")
            return True

    def delete_client_messages(self, client_id):
        """
        Delete all messages for a specific client.
        """
        with self.lock:
            if client_id not in self.client_messages:
                return 0

            msg_ids = self.client_messages[client_id].copy()
            count = 0

            for msg_id in msg_ids:
                if msg_id in self.messages:
                    msg = self.messages[msg_id]

                    if msg.sender_id in self.client_messages:
                        if msg_id in self.client_messages[msg.sender_id]:
                            self.client_messages[msg.sender_id].remove(msg_id)

                    if msg.recipient_id in self.client_messages:
                        if msg_id in self.client_messages[msg.recipient_id]:
                            self.client_messages[msg.recipient_id].remove(msg_id)

                    del self.messages[msg_id]
                    count += 1

            if client_id in self.client_messages and not self.client_messages[client_id]:
                del self.client_messages[client_id]

            print(f"[MESSAGES DELETED] Client {client_id}: {count} messages")
            return count

    def clear_all_messages(self):
        """
        Clear entire message storage.
        """
        with self.lock:
            count = len(self.messages)
            self.messages.clear()
            self.client_messages.clear()
            print(f"[ALL MESSAGES CLEARED] {count} messages deleted")
            return count

    def _auto_delete_expired(self):
        """
        Delete expired messages (internal method).
        """
        with self.lock:
            expired_ids = [
                msg_id for msg_id, msg in self.messages.items()
                if msg.is_expired(self.message_ttl)
            ]

            for msg_id in expired_ids:
                msg = self.messages[msg_id]

                if msg.sender_id in self.client_messages:
                    if msg_id in self.client_messages[msg.sender_id]:
                        self.client_messages[msg.sender_id].remove(msg_id)
                    if not self.client_messages[msg.sender_id]:
                        del self.client_messages[msg.sender_id]

                if msg.recipient_id in self.client_messages:
                    if msg_id in self.client_messages[msg.recipient_id]:
                        self.client_messages[msg.recipient_id].remove(msg_id)
                    if not self.client_messages[msg.recipient_id]:
                        del self.client_messages[msg.recipient_id]

                del self.messages[msg_id]

            if expired_ids:
                print(f"[AUTO-DELETE] {len(expired_ids)} expired messages removed")

            return len(expired_ids)

    def _auto_delete_worker(self):
        """Background worker thread"""
        print(f"[AUTO-DELETE THREAD] Started")

        while self.running:
            time.sleep(self.auto_delete_interval)
            if self.running:
                self._auto_delete_expired()

    def get_stats(self):
        """Get message storage statistics"""
        with self.lock:
            return {
                'total_messages': len(self.messages),
                'total_clients_with_messages': len(self.client_messages),
                'message_ttl_seconds': self.message_ttl,
                'auto_delete_interval_seconds': self.auto_delete_interval
            }

    def stop(self):
        """Stop the message manager"""
        self.running = False
        if self.auto_delete_thread.is_alive():
            self.auto_delete_thread.join(timeout=2)
        print(f"[MESSAGE MANAGER] Stopped")
