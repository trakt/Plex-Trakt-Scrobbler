from sync.pull import Pull
from sync.push import Push
from sync.synchronize import Synchronize
import threading
import time


class SyncManager(object):
    thread = None
    lock = None

    running = False
    current_work = None

    handlers = None

    @classmethod
    def construct(cls):
        cls.thread = threading.Thread(target=cls.run, name="SyncManager")
        cls.lock = threading.Lock()

        cls.handlers = {
            'pull': Pull(),
            'push': Push(),
            'synchronize': Synchronize()
        }

    @classmethod
    def start(cls):
        cls.running = True
        cls.thread.start()

    @classmethod
    def stop(cls):
        cls.running = False

    @classmethod
    def run(cls):
        while cls.running:
            if not cls.current_work:
                time.sleep(3)
                continue

            cls.lock.acquire()

            Log.Debug("Work lock acquired, starting...")

            # run

            Log.Debug("Work finished, releasing lock...")
            cls.current_work = None
            cls.lock.release()

    @classmethod
    def trigger(cls, name, blocking=False, **kwargs):
        if not cls.lock.acquire(blocking):
            return False

        cls.current_work = {
            'name': name,
            'kwargs': kwargs
        }

        cls.lock.release()

        return True

    @classmethod
    def trigger_push(cls):
        return cls.trigger('push')

    @classmethod
    def trigger_pull(cls):
        return cls.trigger('pull')

    @classmethod
    def trigger_synchronize(cls):
        return cls.trigger('synchronize')
