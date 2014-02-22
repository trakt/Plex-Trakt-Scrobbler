from core.helpers import total_seconds, build_repr
from core.model import DictModel


class SyncStatus(DictModel):
    root_key = 'syncStatus'

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

        # Save to disk
        Dict.Save()

    def __repr__(self):
        return build_repr(self, ['previous_timestamp', 'previous_elapsed', 'previous_result', 'last_success_timestamp'])

    def __str__(self):
        return self.__repr__()
