from datetime import datetime
from core.helpers import total_seconds, sum
from data.sync_status import SyncStatus
from sync.pull import Pull
from sync.push import Push
from sync.synchronize import Synchronize
import threading
import time
from sync.task import SyncTask


class SyncManager(object):
    thread = None
    lock = None

    running = False

    current = None

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
            return cls.current.stopping

        def update_progress(*args, **kwargs):
            cls.update_progress(*args, **kwargs)

        for key, handler in cls.handlers.items():
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
            if not cls.current:
                time.sleep(3)
                continue

            cls.acquire()

            if not cls.run_work():
                if cls.current.stopping:
                    Log.Info('Syncing task stopped as requested')
                else:
                    Log.Warn('Error occurred while running work')

            cls.release()

    @classmethod
    def run_work(cls):
        # Get work details
        key = cls.current.key
        kwargs = cls.current.kwargs or {}
        section = kwargs.get('section')

        # Find handler
        handler = cls.handlers.get(key)
        if not handler:
            Log.Warn('Unknown handler "%s"' % key)
            return False

        Log.Debug('Processing work with handler "%s" and kwargs: %s' % (key, kwargs))

        cls.current.start_time = datetime.now()

        try:
            cls.current.success = handler.run(**kwargs)
        except Exception, e:
            cls.current.success = False

            Log.Warn('Exception raised in handler for "%s" (%s): %s' % (
                key, type(e), e)
            )

        cls.current.end_time = datetime.now()

        # Update task status
        status = cls.get_status(key, section)
        status.update(cls.current)
        status.save()

        # Save to disk
        Dict.Save()

        # Return task success result
        return cls.current.success

    @classmethod
    def acquire(cls):
        cls.lock.acquire()
        Log.Debug('Acquired work: %s' % cls.current)

    @classmethod
    def release(cls):
        Log.Debug("Work finished")
        cls.reset()

        cls.lock.release()

    @classmethod
    def reset(cls):
        cls.current = None

    @classmethod
    def get_current(cls):
        current = cls.current

        if not current:
            return None, None

        return current, cls.handlers.get(current.key)

    @classmethod
    def get_status(cls, key, section=None):
        if section:
            key = (key, section)

        status = SyncStatus.load(key)

        if not status:
            status = SyncStatus(key)
            status.save()

        return status

    @classmethod
    def update_progress(cls, current, start=0, end=100):
        statistics = cls.current.statistics

        # Remove offset
        current = current - start
        end = end - start

        # Calculate progress and difference since last update
        progress = float(current) / end
        progress_diff = progress - (statistics.progress or 0)

        if statistics.last_update:
            diff_seconds = total_seconds(datetime.now() - statistics.last_update)

            # Plot current percent/sec
            statistics.plots.append(diff_seconds / (progress_diff * 100))

            # Calculate average percent/sec
            statistics.per_perc = sum(statistics.plots) / len(statistics.plots)

            # Calculate estimated time remaining
            statistics.seconds_remaining = ((1 - progress) * 100) * statistics.per_perc

        Log.Debug('[Sync][Progress] Progress: %02d%%, Estimated time remaining: ~%s seconds' % (
            progress * 100,
            int(round(statistics.seconds_remaining, 0)) if statistics.seconds_remaining else '?'
        ))

        statistics.progress = progress
        statistics.last_update = datetime.now()

    # Trigger

    @classmethod
    def trigger(cls, key, blocking=False, **kwargs):
        if not cls.lock.acquire(blocking):
            return False

        cls.reset()

        cls.current = SyncTask(key, kwargs)

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
        if not cls.current:
            return False

        cls.current.stopping = True
        return True
