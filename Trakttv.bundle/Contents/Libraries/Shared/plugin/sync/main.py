from plugin.sync.core.enums import SyncAction, SyncData
from plugin.sync.modules import *

import logging

log = logging.getLogger(__name__)

MODULES = [
    Collection,
    Playback,
    Ratings,
    Watched
]


class Main(object):
    def __init__(self):
        self.modules = dict(self._construct_modules())

    def _construct_modules(self):
        for module in MODULES:
            if module.__data__ is None:
                log.warn('Module %r is missing a valid "__data__" attribute')
                continue

            yield module.__data__, module(self)

    def start(self, account, action, data, **kwargs):
        """Start a sync for the provided account

        Note: if a sync is already running a `SyncError` will be raised.

        :param account: Account to synchronize with trakt
        :type account: int or plugin.models.Account

        :param action: Syncing action to perform (pull, push)
        :type action: int (plugin.sync.SyncAction)

        :param data: Data to synchronize (collection, ratings, etc..)
        :type data: int (plugin.sync.SyncData)

        :return: `SyncResult` object with details on the sync outcome.
        :rtype: plugin.sync.core.result.SyncResult
        """
        raise NotImplementedError

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
