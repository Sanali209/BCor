import time

class semaphore:
    def __init__(self):
        self._lock = False

    def lock(self):
        self._lock = True

    def unlock(self):
        self._lock = False

    def is_locked(self):
        return self._lock

    def wait(self):
        while self._lock:
            time.sleep(0.1)

    def __enter__(self):
        self.lock()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unlock()

