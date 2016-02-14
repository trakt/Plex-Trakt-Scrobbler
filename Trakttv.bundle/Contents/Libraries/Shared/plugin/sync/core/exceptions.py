class QueueError(Exception):
    def __init__(self, title, message=None):
        self.title = title
        self.message = message

    def __repr__(self):
        return '<QueueError title: %r, message: %r>' % (
            self.title,
            self.message
        )

    def __str__(self):
        return self.message


class SyncAbort(Exception):
    def __init__(self):
        super(SyncAbort, self).__init__('Sync was cancelled')


class SyncError(Exception):
    pass

