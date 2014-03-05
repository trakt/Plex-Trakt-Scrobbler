from core.eventing import EventManager
from core.helpers import total_seconds, sum, get_pref
from core.logger import Logger
from data.sync_status import SyncStatus
from sync.sync_base import CancelException
from sync.sync_task import SyncTask
from sync.pull import Pull
from sync.push import Push
from sync.synchronize import Synchronize
from datetime import datetime
import threading
import traceback
import time


log = Logger('sync.manager')

HANDLERS = [Pull, Push, Synchronize]

# Maps interval option labels to their minute values (argh..)
INTERVAL_MAP = {
    'Disabled':   None,
    '15 Minutes': 15,
    '30 Minutes': 30,
    'Hour':       60,
    '3 Hours':    180,
    '6 Hours':    360,
    '12 Hours':   720,
    'Day':        1440,
    'Week':       10080,
}


class SyncManager(object):
    thread = None
    lock = None

    running = False

    cache_id = None
    current = None

    handlers = None
    statistics = None

    @classmethod
    def initialize(cls):
        cls.thread = threading.Thread(target=cls.run, name="SyncManager")
        cls.lock = threading.Lock()

        EventManager.subscribe('notifications.status.scan_complete', cls.scan_complete)
        EventManager.subscribe('sync.get_cache_id', cls.get_cache_id)

        cls.handlers = dict([(h.key, h(cls)) for h in HANDLERS])
        cls.statistics = SyncStatistics()

    @classmethod
    def get_cache_id(cls):
        return cls.cache_id

    @classmethod
    def get_current(cls):
        current = cls.current

        if not current:
            return None, None

        return current, cls.handlers.get(current.key)

    @classmethod
    def get_status(cls, key, section=None):
        """Retrieve the status of a task

        :rtype : SyncStatus
        """
        if section:
            key = (key, section)

        status = SyncStatus.load(key)

        if not status:
            status = SyncStatus(key)
            status.save()

        return status

    @classmethod
    def reset(cls):
        cls.current = None

    @classmethod
    def start(cls):
        cls.running = True
        cls.thread.start()

    @classmethod
    def stop(cls):
        cls.running = False

    @classmethod
    def acquire(cls):
        cls.lock.acquire()
        log.debug('Acquired work: %s' % cls.current)

    @classmethod
    def release(cls):
        log.debug("Work finished")
        cls.reset()

        cls.lock.release()

    @classmethod
    def check_schedule(cls):
        interval = INTERVAL_MAP.get(Prefs['sync_run_interval'])
        if not interval:
            return False

        status = cls.get_status('synchronize')
        if not status.previous_timestamp:
            return False

        since_run = total_seconds(datetime.utcnow() - status.previous_timestamp) / 60
        if since_run < interval:
            return False

        return cls.trigger_synchronize()

    @classmethod
    def run(cls):
        while cls.running:
            if not cls.current and not cls.check_schedule():
                time.sleep(3)
                continue

            cls.acquire()

            if not cls.run_work():
                if cls.current.stopping:
                    log.info('Syncing task stopped as requested')
                else:
                    log.warn('Error occurred while running work')

            cls.release()

    @classmethod
    def run_work(cls):
        # Get work details
        key = cls.current.key
        kwargs = cls.current.kwargs or {}
        section = kwargs.pop('section', None)

        # Find handler
        handler = cls.handlers.get(key)
        if not handler:
            log.warn('Unknown handler "%s"' % key)
            return False

        log.debug('Processing work with handler "%s" and kwargs: %s' % (key, kwargs))

        # Update cache_id to ensure we trigger new requests
        cls.cache_id = str(time.time())
        success = False

        try:
            success = handler.run(section=section, **kwargs)
        except CancelException, e:
            handler.update_status(False)
            log.info('Task "%s" was cancelled', key)
        except Exception, e:
            handler.update_status(False)

            log.warn('Exception raised in handler for "%s" (%s) %s: %s' % (
                key, type(e), e, traceback.format_exc()
            ))

        # Return task success result
        return success

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
            diff_seconds = total_seconds(datetime.utcnow() - statistics.last_update)

            # Plot current percent/sec
            statistics.plots.append(diff_seconds / (progress_diff * 100))

            # Calculate average percent/sec
            statistics.per_perc = sum(statistics.plots) / len(statistics.plots)

            # Calculate estimated time remaining
            statistics.seconds_remaining = ((1 - progress) * 100) * statistics.per_perc

        log.debug('[Sync][Progress] Progress: %02d%%, Estimated time remaining: ~%s seconds' % (
            progress * 100,
            int(round(statistics.seconds_remaining, 0)) if statistics.seconds_remaining else '?'
        ))

        statistics.progress = progress
        statistics.last_update = datetime.utcnow()

    @classmethod
    def scan_complete(cls):
        if not get_pref('sync_run_library'):
            log.info('"Run after library updates" not enabled, ignoring')
            return

        cls.trigger_synchronize()

    # Trigger

    @classmethod
    def trigger(cls, key, blocking=False, **kwargs):
        # Ensure sync task isn't already running
        if not cls.lock.acquire(blocking):
            return False

        # Ensure account details are set
        if not Prefs['username'] or not Prefs['password']:
            return False

        cls.reset()
        cls.current = SyncTask(key, kwargs)

        cls.lock.release()
        return True

    @classmethod
    def trigger_push(cls, section=None):
        return cls.trigger('push', section=section)

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


class SyncStatistics(object):
    def __init__(self):
        for h in HANDLERS:
            self.bind(h)

    def bind(self, task):
        key = task.get_key()

        EventManager.subscribe(
            'sync.%s.started' % key,
            lambda start, end: self.started(key, start, end)
        )

        EventManager.subscribe(
            'sync.%s.progress' % key,
            lambda value: self.progress(key, value)
        )

        EventManager.subscribe(
            'sync.%s.finished' % key,
            lambda: self.finished(key)
        )

        # Bind child progress events
        for child in task.children:
            self.bind(child)

    def started(self, key, start, end):
        log.debug('SyncStatistics.start(%s, %s, %s)', repr(key), start, end)

    def progress(self, key, value):
        log.debug('SyncStatistics.update(%s, %s)', repr(key), value)

    def finished(self, key):
        log.debug('SyncStatistics.finish(%s)', repr(key))
