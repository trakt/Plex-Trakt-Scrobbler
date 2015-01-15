from core.helpers import build_repr
from plugin.data.model import Model, Property

from jsonpickle.unpickler import ClassRegistry
import trakt


class SyncStatus(Model):
    group = 'SyncStatus'

    error = Property(None)
    exceptions = Property(lambda: [], pickle=False)

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

    def update(self, success, start_time, end_time, exceptions):
        self.previous_success = success
        self.previous_timestamp = start_time
        self.previous_elapsed = end_time - start_time

        if success:
            self.last_success = start_time

        if exceptions:
            if type(exceptions) is not list:
                exceptions = [exceptions]

            self.error = self.format_exception(exceptions[0])
            self.exceptions = exceptions
        else:
            self.error = None
            self.exceptions = []

        self.save()

    @staticmethod
    def format_exception(exc):
        if isinstance(exc, trakt.RequestError):
            # trakt.py
            _, desc = exc.error if len(exc.error) == 2 else ("Unknown", "Unknown")

            # Format message
            return 'trakt.tv - %s: "%s"' % (exc.status_code, desc)

        return '%s: "%s"' % (getattr(type(exc), '__name__'), exc.message)

    def __repr__(self):
        return build_repr(self, [
            'previous_timestamp', 'previous_elapsed',
            'previous_success', 'last_success'
        ])

    def __str__(self):
        return self.__repr__()

ClassRegistry.register('sync_status.SyncStatus', SyncStatus)
