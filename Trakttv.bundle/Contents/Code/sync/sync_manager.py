from core.cache import CacheManager
from core.helpers import total_seconds, get_pref
from core.localization import localization
from core.logger import Logger
from data.sync_status import SyncStatus
from plugin.core.event import Global as EG
from sync.sync_base import CancelException
from sync.sync_statistics import SyncStatistics
from sync.sync_task import SyncTask
from sync.pull import Pull
from sync.push import Push
from sync.synchronize import Synchronize

from datetime import datetime
from plex import Plex
from plex_activity import Activity
import gc
import threading
import traceback
import time
import uuid

L, LF = localization('sync.manager')
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
    initialized = False
    thread = None
    lock = None

    running = False

    current = None

    handlers = None
    statistics = None

    @classmethod
    def initialize(cls):
        cls.thread = threading.Thread(target=cls.run, name="SyncManager")
        cls.lock = threading.Lock()

        cls.handlers = dict([(h.key, h(cls)) for h in HANDLERS])
        cls.statistics = SyncStatistics(cls)

        # Load/setup matcher cache
        Plex.configuration.defaults.cache(
            matcher=CacheManager.get('matcher', persistent=True)
        )

        # Bind activity events
        Activity.on('websocket.scanner.finished', cls.scanner_finished)

        EG['SyncManager.current'].set(lambda: cls.current)

        cls.initialized = True

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
            # Ensure manager has been initialized
            if not cls.initialized:
                time.sleep(3)
                continue

            # Check for scheduled syncing
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
        kwargs = cls.current.kwargs.copy() or {}
        section = kwargs.pop('section', None)

        # Find handler
        handler = cls.handlers.get(key)
        if not handler:
            log.error('Unknown handler "%s"' % key)
            return False

        log.debug('Processing work with sid "%s" (handler: %r, kwargs: %r)' % (cls.current.sid, key, kwargs))

        success = False

        try:
            success = handler.run(section=section, **kwargs)
        except CancelException, e:
            handler.update_status(False)

            log.info('Task "%s" was cancelled', key)
        except Exception, ex:
            handler.update_status(False)

            log.error('Exception raised in handler for %r: %s', key, ex, exc_info=True)

        log.debug(
            'Cache Statistics - len(matcher): %s, len(metadata): %s',
            len(CacheManager.get('matcher')),
            len(CacheManager.get('metadata'))
        )

        # Sync "matcher" cache (back to disk)
        CacheManager.get('matcher').sync()

        # Clear memory caches
        CacheManager.get('matcher').cache.clear()
        CacheManager.get('metadata').cache.clear()

        # Run garbage collection
        log.debug('[GC] Collected %d objects', gc.collect())
        log.debug('[GC] Count: %s', gc.get_count())
        log.debug('[GC] Garbage: %s', len(gc.garbage))

        # Return task success result
        return success

    @classmethod
    def scanner_finished(cls):
        if not get_pref('sync_run_library'):
            log.debug('"Run after library updates" not enabled, ignoring')
            return

        cls.trigger_synchronize()

    # Trigger

    @classmethod
    def trigger(cls, key, blocking=False, **kwargs):
        # Ensure manager is initialized
        if not cls.initialized:
            log.warn(L('not_initialized'))
            return False, L('not_initialized')

        # Ensure sync task isn't already running
        if not cls.lock.acquire(blocking):
            return False, L('already_running')

        # Ensure account details are set
        if not get_pref('valid'):
            cls.lock.release()
            return False, L('invalid_credentials')

        cls.reset()
        cls.current = SyncTask(key, kwargs)

        cls.lock.release()
        return True, ''

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
