import threading


class ThreadSafeInt:
    def __init__(self, default_value: int):
        self.lock = threading.Lock()
        self.value = default_value

    def increment(self):
        with self.lock:
            self.value += 1

    def decrement(self):
        with self.lock:
            self.value -= 1

    def set(self, val):
        with self.lock:
            self.value = val

    def get(self):
        with self.lock:
            return self.value
