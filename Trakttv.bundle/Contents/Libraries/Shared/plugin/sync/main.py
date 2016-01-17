from threading import Thread
from plugin.models import SyncResult
from plugin.sync.core.enums import SyncMedia
from plugin.sync.core.exceptions import QueueError
from plugin.sync.core.task import SyncTask
from plugin.sync.handlers import *
from plugin.sync.modes import *
from plugin.sync.triggers import LibraryUpdateTrigger

from threading import Lock
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
        try:
            # Create new task
            task = SyncTask.create(account, mode, data, media, trigger, **kwargs)
        except Exception, ex:
            log.warn('Unable to construct task: %s', ex, exc_info=True)
            raise QueueError("Error", "Unable to construct task")

        with self._queue_lock:
            # Ensure we only have one task queued per account
            account_tasks = [t for (p, a, t) in self._queue.queue if a == task.account.id]

            if len(account_tasks):
                raise QueueError("Unable to queue sync", "Sync has already been queued for this account")

            # Queue task until the thread is available
            self._queue.put((priority, task.account.id, task), block=False)

            # Ensure thread is active
            self.spawn()

        # Wait for task start
        for x in xrange(3):
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
            # Retrieve task from queue
            try:
                _, _, self.current = self._queue.get(timeout=30)
            except Queue.Empty:
                continue

            # Start task
            log.info('(%r) Started', self.current.mode)
            self.current.started = True

            try:
                # Construct modes/handlers for task
                self.current.construct(HANDLERS, MODES)

                # Run in plex authorization context
                with self.current.account.plex.authorization():
                    # Run in trakt authorization context
                    with self.current.account.trakt.authorization():
                        # Run sync
                        self.run()

                self.current.success = True
            except Exception, ex:
                log.warn('Exception raised in run(): %s', ex, exc_info=True)

                self.current.exceptions.append(sys.exc_info())
                self.current.success = False

            try:
                # Sync task complete, run final tasks
                self.finish()
            except Exception, ex:
                log.error('Unable to run final sync tasks: %s', ex, exc_info=True)

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
