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

    def update(self, task):
        self.previous_success = task.success
        self.previous_timestamp = task.start_time
        self.previous_elapsed = task.end_time - task.start_time

        if task.success:
            self.last_success = task.start_time

    def __repr__(self):
        return build_repr(self, ['previous_timestamp', 'previous_elapsed', 'previous_result', 'last_success_timestamp'])

    def __str__(self):
        return self.__repr__()
