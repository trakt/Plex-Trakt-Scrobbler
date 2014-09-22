from trakt.interfaces.sync.core.mixins import Get, Add, Remove


class SyncCollectionInterface(Get, Add, Remove):
    path = 'sync/collection'
    flags = {'is_collected': True}
