from plugin.core.message import InterfaceMessages
from plugin.models import SyncResult
from plugin.modules.core.manager import ModuleManager
from plugin.preferences import Preferences
from plugin.sync.core.enums import SyncMedia
from plugin.sync.core.exceptions import QueueError
from plugin.sync.core.task import SyncTask
from plugin.sync.handlers import *
from plugin.sync.modes import *
from plugin.sync.triggers import LibraryUpdateTrigger

from datetime import datetime, timedelta
from plex_database.library import TZ_LOCAL
from threading import Lock, Thread
import logging
import Queue
import sys
import time

log = logging.getLogger(__name__)

HANDLERS = [
    Collection,
    List,
    Playback,
    Ratings,
    Watched
]

MODES = [
    FastPull,
    Full,
    Pull,
    Push
]

# Display error if the system timezone is not available
if TZ_LOCAL is None:
    InterfaceMessages.add(logging.ERROR, 'Unable to retrieve system timezone, syncing will not be available')


class Main(object):
    def __init__(self):
        self.current = None

        self._queue = Queue.PriorityQueue()
        self._queue_lock = Lock()

        self._spawn_lock = Lock()
        self._thread = None

        # Triggers
        self._library_update = LibraryUpdateTrigger(self)

    def queue(self, account, mode, data=None, media=SyncMedia.All, priority=10, trigger=SyncResult.Trigger.Manual, **kwargs):
        """Queue a sync for the provided account

        Note: if a sync is already queued for the provided account a `SyncError` will be raised.

        :param account: Account to synchronize with trakt
        :type account: int or plugin.models.Account

        :param mode: Syncing mode (pull, push, etc..)
        :type mode: int (plugin.sync.SyncMode)

        :param data: Data to synchronize (collection, ratings, etc..)
        :type data: int (plugin.sync.SyncData)

        :param media: Media to synchronize (movies, shows, etc..)
        :type media: int (plugin.sync.SyncMedia)

        :return: `SyncResult` object with details on the sync outcome.
        :rtype: plugin.sync.core.result.SyncResult
        """
        if InterfaceMessages.critical:
            raise QueueError('Error', InterfaceMessages.message)

        if TZ_LOCAL is None:
            raise QueueError('Error', 'Unable to retrieve system timezone')

        try:
            # Create new task
            task = SyncTask.create(account, mode, data, media, trigger, **kwargs)
        except Exception as ex:
            log.warn('Unable to construct task: %s', ex, exc_info=True)

            # Raise as queue error
            raise QueueError('Error', 'Unable to construct task: %s' % ex)

        with self._queue_lock:
            # Ensure we only have one task queued per account
            account_tasks = [
                t for (p, a, t) in self._queue.queue
                if (
                    a == task.account.id and
                    t.result and
                    (trigger != SyncResult.Trigger.Manual or t.result.trigger == trigger)
                )
            ]

            if len(account_tasks):
                raise QueueError("Unable to queue sync", "Sync has already been queued for this account")

            # Queue task until the thread is available
            self._queue.put((priority, task.account.id, task), block=False)

            # Ensure thread is active
            self.spawn()

        # Wait for task start
        for x in xrange(10):
            if task.started:
                log.debug('Task %r has started', task)
                return

            time.sleep(1)

        raise QueueError("Sync queued", "Sync will start once the currently queued tasks have finished")

    def spawn(self):
        """Ensure syncing thread has been spawned"""
        with self._spawn_lock:
            if self._thread is not None:
                return

            self._thread = Thread(target=self.run_wrapper)
            self._thread.start()

            log.debug('Spawned syncing thread: %r', self._thread)

    def run_wrapper(self):
        while True:
            try:
                # Retrieve task from queue
                try:
                    priority, account_id, task = self._queue.get(timeout=30)
                except Queue.Empty:
                    continue

                # Check if we should defer this task
                if self.should_defer(task):
                    # Re-queue sync task
                    if priority < 10000:
                        priority += 1

                    self._queue.put((priority, account_id, task), block=False)

                    # Wait 10 seconds
                    time.sleep(10)
                    continue

                # Select task
                self.current = task
            except Exception as ex:
                log.warn('Exception raised while attempting to retrieve sync task from queue: %s', ex, exc_info=True)

                time.sleep(30)
                continue

            # Start task
            try:
                log.info('(%r) Started', self.current.mode)
                self.current.started = True

                # Construct modes/handlers for task
                self.current.construct(HANDLERS, MODES)

                # Run in plex authorization context
                with self.current.account.plex.authorization():
                    # Run in trakt authorization context
                    with self.current.account.trakt.authorization():
                        # Run sync
                        self.run()

                self.current.success = True
            except Exception as ex:
                log.warn('Exception raised in sync task: %s', ex, exc_info=True)

                self.current.exceptions.append(sys.exc_info())
                self.current.success = False

            try:
                # Sync task complete, run final tasks
                self.finish()
            except Exception as ex:
                log.error('Exception raised while attempting to finish sync task: %s', ex, exc_info=True)

    def should_defer(self, task):
        if task and task.result:
            # Ignore sync conditions on manual triggers
            if task.result.trigger == SyncResult.Trigger.Manual:
                return False

            # Ignore sync conditions if the task has been queued for over 12 hours
            started_ago = datetime.utcnow() - task.result.started_at

            if started_ago > timedelta(hours=12):
                log.debug('Task has been queued for over 12 hours, ignoring sync conditions')
                return False

        if Preferences.get('sync.idle_defer'):
            # Defer sync tasks until server finishes streaming (and is idle for 30 minutes)
            if ModuleManager['sessions'].is_streaming():
                log.debug('Deferring sync task, server is currently streaming media')
                return True

            if not ModuleManager['sessions'].is_idle():
                log.debug(
                    'Deferring sync task, server has been streaming media recently (in the last %d minutes)',
                    Preferences.get('sync.idle_delay')
                )
                return True

        return False

    def finish(self):
        # Cleanup `current` task
        current = self.current
        current.finish()

        # Task finished
        log.info('(%r) Done', current.mode)

        # Cleanup sync manager
        self.current = None

    def cancel(self, id):
        """Trigger a currently running sync to abort

        Note: A sync will only cancel at the next "safe" cancel point, this will not
        force a thread to end immediately.

        :return: `True` if a sync has been triggered to cancel,
                 `False` if there was no sync to cancel.
        :rtype: bool
        """
        current = self.current

        if current is None:
            # No active sync task
            return True

        if current.id != id:
            # Active task doesn't match `id`
            return False

        # Request task abort
        current.abort(timeout=10)

        log.info('(%r) Abort', current.mode)
        return True

    def run(self):
        # Trigger sync methods
        self._trigger([
            'construct',
            'start',
            'run',
            'finish',
            'stop'
        ])

    def _trigger(self, names):
        if self.current.mode not in self.current.modes:
            log.warn('Unknown sync mode: %r', self.current.mode)
            return

        mode = self.current.modes[self.current.mode]

        for name in names:
            func = getattr(mode, name, None)

            if not func:
                log.warn('Unknown method: %r', name)
                return

            func()


Sync = Main()
