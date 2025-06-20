import time
import threading
from functools import wraps

def rate_limited(min_interval_seconds):

    lock = threading.Lock()
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                elapsed = time.time() - last_called[0]
                wait_time = min_interval_seconds - elapsed
                if wait_time > 0:
                    time.sleep(wait_time)
                last_called[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator
