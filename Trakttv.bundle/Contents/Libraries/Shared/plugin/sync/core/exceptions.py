class SyncAbort(Exception):
    def __init__(self):
        super(SyncAbort, self).__init__('Sync was cancelled')


class SyncError(Exception):
    pass
