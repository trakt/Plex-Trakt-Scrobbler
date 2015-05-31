from threading import Thread
from plugin.sync.core.task import SyncTask
from plugin.sync.handlers import *
from plugin.sync.modes import *

import logging
import sys

log = logging.getLogger(__name__)

HANDLERS = [
    Collection,
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
        self.handlers = dict(self._construct_modules(HANDLERS, 'data'))
        self.modes = dict(self._construct_modules(MODES, 'mode'))

        self.current = None
        self.thread = None

    def _construct_modules(self, modules, attribute):
        for cls in modules:
            key = getattr(cls, attribute, None)

            if key is None:
                log.warn('Module %r is missing a valid %r attribute', cls, attribute)
                continue

            yield key, cls(self)

    def start(self, account, mode, data, media, **kwargs):
        """Start a sync for the provided account

        Note: if a sync is already running a `SyncError` will be raised.

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
        self.current = SyncTask.create(account, mode, data, media, **kwargs)

        self.thread = Thread(target=self.run_wrapper)
        self.thread.start()

        return None, None

    def run_wrapper(self):
        if self.current is None:
            log.warn('Missing "current" sync task')
            return

        log.info('(%r) Started', self.current.mode)

        try:
            # Run in trakt authorization context
            with self.current.account.trakt.authorization():
                self.run()
        except Exception, ex:
            log.warn('Exception raised in run(): %s', ex, exc_info=True)

            self.current.exceptions.append(sys.exc_info())
            self.current.success = False

        # Sync task complete, run final tasks
        self.current.finish()

        log.info('(%r) Done', self.current.mode)

        # Cleanup sync manager
        self.current = None

    def run(self):
        if self.current.mode not in self.modes:
            log.warn('Unknown sync mode: %r', self.current.mode)
            return

        self.modes[self.current.mode].run()

    def cancel(self):
        """Trigger a currently running sync to cancel

        Note: A sync will only cancel at the next "safe" cancel point, this will not
        force a thread to end immediately.

        :return: `True` if a sync has been triggered to cancel,
                 `False` if there was no sync to cancel.
        :rtype: bool
        """
        raise NotImplementedError


Sync = Main()
