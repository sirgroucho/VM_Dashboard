import json
import threading
import time
from typing import Dict, List, Callable, Optional
from queue import Queue, Empty
from datetime import datetime

class LogEventBus:
    """Thread-safe event bus for Server-Sent Events."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()
        self._heartbeat_interval = 30  # seconds
        
    def subscribe(self, client_id: str, callback: Callable):
        """Subscribe a client to log events."""
        with self._lock:
            if client_id not in self._subscribers:
                self._subscribers[client_id] = []
            self._subscribers[client_id].append(callback)
    
    def unsubscribe(self, client_id: str, callback: Callable):
        """Unsubscribe a client from log events."""
        with self._lock:
            if client_id in self._subscribers:
                try:
                    self._subscribers[client_id].remove(callback)
                    if not self._subscribers[client_id]:
                        del self._subscribers[client_id]
                except ValueError:
                    pass
    
    def publish(self, event_data: dict):
        """Publish a log event to all subscribers."""
        with self._lock:
            for client_id, callbacks in self._subscribers.items():
                for callback in callbacks:
                    try:
                        callback(event_data)
                    except Exception as e:
                        # Log error but don't crash
                        print(f"Error sending event to {client_id}: {e}")
    
    def get_subscriber_count(self) -> int:
        """Get total number of active subscribers."""
        with self._lock:
            return sum(len(callbacks) for callbacks in self._subscribers.values())
    
    def cleanup_dead_connections(self):
        """Clean up dead connections (called periodically)."""
        # This could be enhanced to detect dead connections
        pass

class SSEManager:
    """Manages Server-Sent Events for log streaming."""
    
    def __init__(self, event_bus: LogEventBus):
        self.event_bus = event_bus
        self._clients: Dict[str, 'SSEClient'] = {}
        self._lock = threading.RLock()
    
    def create_client(self, client_id: str, filters: Optional[dict] = None) -> 'SSEClient':
        """Create a new SSE client."""
        client = SSEClient(client_id, filters, self.event_bus)
        with self._lock:
            self._clients[client_id] = client
        return client
    
    def remove_client(self, client_id: str):
        """Remove an SSE client."""
        with self._lock:
            if client_id in self._clients:
                self._clients[client_id].close()
                del self._clients[client_id]
    
    def get_client_count(self) -> int:
        """Get number of active clients."""
        with self._lock:
            return len(self._clients)

class SSEClient:
    """Individual SSE client connection."""
    
    def __init__(self, client_id: str, filters: Optional[dict], event_bus: LogEventBus):
        self.client_id = client_id
        self.filters = filters or {}
        self.event_bus = event_bus
        self._queue = Queue(maxsize=100)
        self._closed = False
        
        # Subscribe to events
        self.event_bus.subscribe(client_id, self._on_event)
    
    def _on_event(self, event_data: dict):
        """Handle incoming events from the bus."""
        if self._closed:
            return
        
        # Apply filters
        if self._should_send_event(event_data):
            try:
                self._queue.put_nowait(event_data)
            except Queue.Full:
                # Drop oldest event if queue is full
                try:
                    self._queue.get_nowait()
                    self._queue.put_nowait(event_data)
                except Queue.Empty:
                    pass
    
    def _should_send_event(self, event_data: dict) -> bool:
        """Check if event should be sent based on filters."""
        if not self.filters:
            return True
        
        # Server ID filter
        if 'server_id' in self.filters and event_data.get('server_id') != self.filters['server_id']:
            return False
        
        # Event type filter
        if 'event_type' in self.filters and event_data.get('event_type') != self.filters['event_type']:
            return False
        
        # Severity filter
        if 'severity' in self.filters and event_data.get('severity') != self.filters['severity']:
            return False
        
        return True
    
    def get_event(self, timeout: float = 30.0) -> Optional[dict]:
        """Get next event, with timeout."""
        if self._closed:
            return None
        
        try:
            return self._queue.get(timeout=timeout)
        except Empty:
            return None
    
    def close(self):
        """Close the client connection."""
        if not self._closed:
            self._closed = True
            self.event_bus.unsubscribe(self.client_id, self._on_event)

# Global event bus instance
log_event_bus = LogEventBus()
sse_manager = SSEManager(log_event_bus)
