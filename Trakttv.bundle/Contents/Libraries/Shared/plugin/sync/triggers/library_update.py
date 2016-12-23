from plugin.models import Account, SyncResult
from plugin.preferences import Preferences
from plugin.sync.core.enums import SyncMode
from plugin.sync.core.exceptions import QueueError
from plugin.sync.triggers.core.base import Trigger

from datetime import datetime, timedelta
from dateutil.tz import tzutc
from plex_activity import Activity
from threading import Lock, Thread
import logging
import time


log = logging.getLogger(__name__)

TRIGGER_DELAY = 60 * 2


class LibraryUpdateTrigger(Trigger):
    def __init__(self, sync):
        super(LibraryUpdateTrigger, self).__init__(sync)

        self._state = LibraryState()
        self._trigger_lock = Lock()

        self._activity_at = None
        self._thread = None

        # Bind to scanner/timeline events
        Activity.on('websocket.scanner.finished', self.trigger)
        Activity.on('websocket.timeline.loading', self.trigger)
        Activity.on('websocket.timeline.finished', self.trigger)

    def trigger(self, *args, **kwargs):
        with self._trigger_lock:
            return self._trigger()

    def _trigger(self):
        log.debug('Scanner activity, sync will be triggered in %d seconds', TRIGGER_DELAY)

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
        except Exception as ex:
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
        except Exception as ex:
            log.error('Unable to queue sync: %s', ex, exc_info=True)

        # Reset state
        self._activity_at = None
        self._thread = None

    def _queue(self):
        started_at = self._state.started_at

        if started_at:
            log.info('Scanner started at: %r', started_at)

        # Retrieve accounts
        accounts = Account.select(
            Account.id
        ).where(
            Account.id > 0
        )

        # Trigger sync on enabled accounts
        for account in accounts:
            if account.deleted:
                continue

            # Ensure account has the library update trigger enabled
            enabled = Preferences.get('sync.library_update', account)

            if not enabled:
                continue

            # Retrieve recently added items
            items_added = self._state.get(account.id).pop_added()

            log.info(
                'Detected %d item(s) have been added for account %r',
                account.id,
                len(items_added)
            )

            # Build pull parameters
            pull = {
                # Run pull on items we explicitly know have been created
                'ids': set(items_added)
            }

            if started_at:
                # Run pull on items created since the scanner started
                pull['created_since'] = started_at - timedelta(seconds=30)

            # Queue sync for account
            try:
                self.sync.queue(
                    account=account,
                    mode=SyncMode.Full,

                    priority=100,
                    trigger=SyncResult.Trigger.LibraryUpdate,

                    pull=pull
                )
            except QueueError as ex:
                log.info('Queue error: %s', ex)

                # Unable to queue sync, add items back to the account library state
                self._state.get(account.id).extend_added(items_added)
            finally:
                # Reset library state
                self._state.reset()


class LibraryState(object):
    def __init__(self):
        self._accounts = {}
        self._accounts_lock = Lock()

        self._started_at = None

        # Bind to activity events
        Activity.on('websocket.scanner.started', self.on_started)
        Activity.on('websocket.timeline.created', self.on_added)

    @property
    def started_at(self):
        return self._started_at

    def get(self, account_id):
        with self._accounts_lock:
            if account_id not in self._accounts:
                self._accounts[account_id] = AccountLibraryState(account_id)

            return self._accounts[account_id]

    def reset(self):
        self._started_at = None

    def on_started(self, *args, **kwargs):
        log.debug('Scanner started')

        self._started_at = datetime.utcnow().replace(tzinfo=tzutc())

    def on_added(self, data, *args, **kwargs):
        if data.get('type') not in [1, 2, 4]:
            return

        log.debug(
            'Item added: %s (id: %r, type: %r)',
            data.get('title'),
            data.get('itemID'),
            data.get('type')
        )

        # Retrieve accounts
        accounts = Account.select(
            Account.id
        ).where(
            Account.id > 0
        )

        # Update library state for accounts
        for account in accounts:
            if account.deleted:
                continue

            # Ensure account has the library update trigger enabled
            enabled = Preferences.get('sync.library_update', account)

            if not enabled:
                continue

            # Update library state for account
            self.get(account.id).on_added(data)


class AccountLibraryState(object):
    def __init__(self, account_id):
        self.account_id = account_id

        self._items_added = []
        self._items_added_lock = Lock()

    def extend_added(self, items):
        with self._items_added_lock:
            self._items_added.extend(items)

    def pop_added(self):
        with self._items_added_lock:
            # Retrieve current items
            items = self._items_added

            # Reset state
            self._items_added = []

        return items

    def on_added(self, data, *args, **kwargs):
        if not data or not data.get('itemID'):
            return

        log.debug(
            'Item added for account %r: %s (id: %r, type: %r)',
            self.account_id,
            data.get('title'),
            data.get('itemID'),
            data.get('type')
        )

        # Append item to list
        with self._items_added_lock:
            self._items_added.append(data.get('itemID'))
