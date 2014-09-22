from trakt.interfaces.sync.core.mixins import Add, Remove


class SyncHistoryInterface(Add, Remove):
    path = 'sync/history'
