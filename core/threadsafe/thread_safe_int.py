import threading


class ThreadSafeInt:
    lock: threading.Lock
    value: int

    def __init__(self, default_value: int):
        self.lock = threading.Lock()
        self.value = default_value

    def increment(self, amnt=1):
        with self.lock:
            self.value += amnt

    def decrement(self, amnt=1):
        with self.lock:
            self.value -= amnt

    def set(self, val):
        with self.lock:
            self.value = val

    def get(self):
        with self.lock:
            return self.value
