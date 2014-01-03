from core.helpers import total_seconds
from core.model import DictModel


class SyncStatus(DictModel):
    root_key = 'syncStatus'

    def __init__(self, handler_key=None):
        """Holds the status of syncing tasks

        :type handler_key: str
        """

        super(SyncStatus, self).__init__(handler_key)

        #: :type: datetime
        self.last_run = None

        #: :type: int
        self.last_elapsed = None

        #: :type: bool
        self.last_success = None

    def update(self, task):
        self.last_success = task.success
        self.last_run = task.start_time
        self.last_elapsed = task.end_time - task.start_time
