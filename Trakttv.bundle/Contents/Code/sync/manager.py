from datetime import datetime
from core.helpers import total_seconds, sum
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
    current_status = None
    current_stopping = False

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

        cls.bind_handlers()

    @classmethod
    def bind_handlers(cls):
        def is_stopping():
            return cls.current_stopping

        def update_progress(*args, **kwargs):
            cls.update_progress(*args, **kwargs)

        for name, handler in cls.handlers.items():
            handler.is_stopping = is_stopping
            handler.update_progress = update_progress

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

            cls.acquire()

            if not cls.run_work():
                if cls.current_stopping:
                    Log.Info('Syncing task stopped as requested')
                else:
                    Log.Warn('Error occurred while running work')

            cls.release()

    @classmethod
    def run_work(cls):
        # Get work details
        handler_name = cls.current_work.get('name')
        kwargs = cls.current_work.get('kwargs', {})

        # Find handler
        handler = cls.handlers.get(handler_name)
        if not handler:
            Log.Warn('Unknown handler "%s"' % handler_name)
            return False

        Log.Debug('Processing work with handler "%s" and kwargs: %s' % (handler_name, kwargs))

        try:
            return handler.run(**kwargs)
        except Exception, e:
            Log.Warn('Exception raised in handler for "%s" (%s): %s' % (
                handler_name, type(e), e)
            )

        return False

    @classmethod
    def acquire(cls):
        cls.lock.acquire()
        Log.Debug('Acquired work: %s' % cls.current_work)

    @classmethod
    def release(cls):
        Log.Debug("Work finished")
        cls.reset()

        cls.lock.release()

    @classmethod
    def reset(cls):
        cls.current_work = None

        cls.current_status = {
            'progress': None,

            'time': {
                'remaining': None,
                'total': None,
            },

            'per_perc': {
                'plots': [],
                'current': None
            },

            'last_update': None
        }

        cls.current_stopping = False

    @classmethod
    def get_active(cls):
        current_work, current_status = cls.current_work, cls.current_status

        if not current_work or not current_status:
            return None, None, None

        return current_work, current_status, cls.handlers.get(current_work.get('name'))

    @classmethod
    def update_progress(cls, current, start=0, end=100):
        # Remove offset
        current = current - start
        end = end - start

        # Calculate progress and difference since last update
        progress = float(current) / end
        progress_diff = progress - (cls.current_status['progress'] or 0)

        last_update = cls.current_status['last_update']
        seconds_remaining = None

        if last_update:
            diff_seconds = total_seconds(datetime.now() - last_update)

            # Plot current percent/sec
            plots = cls.current_status['per_perc']['plots']
            plots.append(diff_seconds / (progress_diff * 100))

            # Calculate average percent/sec
            per_perc_avg = sum(plots) / len(plots)
            cls.current_status['per_perc']['current'] = per_perc_avg

            # Calculate estimated time remaining
            seconds_remaining = ((1 - progress) * 100) * per_perc_avg
            cls.current_status['time']['remaining'] = seconds_remaining

        Log.Debug('[Sync][Progress] Progress: %02d%%, Estimated time remaining: ~%s seconds' % (
            progress * 100,
            int(round(seconds_remaining, 0)) if seconds_remaining else '?'
        ))

        cls.current_status['progress'] = progress
        cls.current_status['last_update'] = datetime.now()

    # Trigger

    @classmethod
    def trigger(cls, name, blocking=False, **kwargs):
        if not cls.lock.acquire(blocking):
            return False

        cls.reset()

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

    # Cancel

    @classmethod
    def cancel(cls):
        if not cls.current_work:
            return False

        cls.current_stopping = True
        return True
