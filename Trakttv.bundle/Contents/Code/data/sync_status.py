from core.helpers import build_repr
from plugin.data.model import Model

from jsonpickle.unpickler import ClassRegistry


class SyncStatus(Model):
    group = 'SyncStatus'

    def __init__(self, handler_key=None):
        """Holds the status of syncing tasks

        :type handler_key: str
        """

        super(SyncStatus, self).__init__(handler_key)

        #: :type: datetime
        self.previous_timestamp = None

        #: :type: int
        self.previous_elapsed = None

        #: :type: bool
        self.previous_success = None

        #: :type: datetime
        self.last_success = None

    def update(self, success, start_time, end_time):
        self.previous_success = success
        self.previous_timestamp = start_time
        self.previous_elapsed = end_time - start_time

        if success:
            self.last_success = start_time

        self.save()

    def __repr__(self):
        return build_repr(self, [
            'previous_timestamp', 'previous_elapsed',
            'previous_success', 'last_success'
        ])

    def __str__(self):
        return self.__repr__()

ClassRegistry.register('sync_status.SyncStatus', SyncStatus)
