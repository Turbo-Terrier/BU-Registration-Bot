import threading

"""
Thread-safe boolean object that uses locks
to maintain proper state.
"""
class ThreadSafeBoolean:
    flag: bool

    def __init__(self):
        self.lock = threading.Lock()
        self.flag = False

    def get_flag(self):
        with self.lock:
            return self.flag

    def set_flag(self, value):
        with self.lock:
            self.flag = value

    def toggle_flag(self):
        with self.lock:
            self.flag = not self.flag
