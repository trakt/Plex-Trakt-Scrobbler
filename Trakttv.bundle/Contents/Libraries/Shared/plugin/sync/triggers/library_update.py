from plugin.models import Account, SyncResult
from plugin.preferences import Preferences
from plugin.sync.core.enums import SyncMode
from plugin.sync.core.exceptions import QueueError
from plugin.sync.triggers.core.base import Trigger

from plex_activity import Activity
from threading import Lock, Thread
import logging
import time

log = logging.getLogger(__name__)

TRIGGER_DELAY = 60 * 2


class LibraryUpdateTrigger(Trigger):
    def __init__(self, sync):
        super(LibraryUpdateTrigger, self).__init__(sync)

        self._activity_at = None
        self._lock = Lock()

        self._thread = None

        # Bind to scanner/timeline events
        Activity.on('websocket.scanner.finished', self.trigger)

        Activity.on('websocket.timeline.loading', self.trigger)
        Activity.on('websocket.timeline.finished', self.trigger)

    def trigger(self, *args, **kwargs):
        with self._lock:
            return self._trigger()

    def _trigger(self):
        log.debug('Detected scanner activity, sync will be triggered in %d seconds', TRIGGER_DELAY)

        # Bump trigger
        self._activity_at = time.time()

        # Ensure thread has started
        self._start()

    def _start(self):
        if self._thread is not None:
            return

        # Construct thread
        self._thread = Thread(target=self._run, name='LibraryUpdateTrigger')
        self._thread.daemon = True

        self._thread.start()

    def _run_wrapper(self):
        try:
            self._run()
        except Exception, ex:
            log.error('Exception raised in _run(): %s', ex, exc_info=True)

    def _run(self):
        while True:
            if self._activity_at is None:
                log.debug('Invalid activity timestamp, cancelling sync trigger')
                return

            # Calculate seconds since last activity
            since = time.time() - self._activity_at

            # Check if scanner is complete
            if since >= TRIGGER_DELAY:
                # Break out of loop to trigger a sync
                break

            # Waiting until metadata has finished downloading
            time.sleep(float(TRIGGER_DELAY) / 6)

        try:
            self._queue()
        except Exception, ex:
            log.error('Unable to queue sync: %s', ex, exc_info=True)

        # Reset state
        self._activity_at = None
        self._thread = None

    def _queue(self):
        accounts = Account.select(
            Account.id
        ).where(
            Account.id > 0
        )

        for account in accounts:
            if account.deleted:
                # Ignore library update trigger for deleted accounts
                continue

            enabled = Preferences.get('sync.library_update', account)

            log.debug('account: %r, enabled: %r', account.id, enabled)

            if not enabled:
                continue

            try:
                # Queue sync for account
                self.sync.queue(
                    account=account,
                    mode=SyncMode.Full,

                    priority=100,
                    trigger=SyncResult.Trigger.LibraryUpdate
                )
            except QueueError, ex:
                log.info('Queue error: %s', ex)
