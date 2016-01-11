class Trigger(object):
    def __init__(self, sync):
        self._sync = sync

    @property
    def sync(self):
        return self._sync
