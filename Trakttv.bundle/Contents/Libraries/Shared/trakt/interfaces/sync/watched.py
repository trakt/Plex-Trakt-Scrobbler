from trakt.interfaces.sync.core.mixins import Get


class SyncWatchedInterface(Get):
    path = 'sync/watched'
    flags = {'is_watched': True}
