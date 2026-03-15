import time
import threading


class EventBus:

    def __init__(self):

        # Store events
        self.events = []

        # Subscribers (listeners)
        self.subscribers = []

        # Thread safety
        self.lock = threading.Lock()

    # -----------------------------------------
    # Emit Event
    # -----------------------------------------

    def emit(self, event_type, data):

        event = {
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        }

        with self.lock:
            self.events.append(event)

        # Notify subscribers
        for callback in self.subscribers:
            try:
                callback(event)
            except Exception as e:
                print(f"[EventBus] subscriber error: {e}")

        return event

    # -----------------------------------------
    # Subscribe Listener
    # -----------------------------------------

    def subscribe(self, callback):

        if callback not in self.subscribers:
            self.subscribers.append(callback)

    # -----------------------------------------
    # Get All Events
    # -----------------------------------------

    def get_events(self):

        with self.lock:
            return list(self.events)

    # -----------------------------------------
    # Clear Events
    # -----------------------------------------

    def clear(self):

        with self.lock:
            self.events = []


# Global singleton
event_bus = EventBus()