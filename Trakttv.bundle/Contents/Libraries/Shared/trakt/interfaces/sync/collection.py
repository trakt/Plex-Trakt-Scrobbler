from trakt.interfaces.sync.base import SyncBaseInterface


class SyncCollectionInterface(SyncBaseInterface):
    path = 'sync/collection'
    flags = {'is_collected': True}
