from oem.core.providers.base import Provider
from oem_core.core.plugin import PluginManager

import logging

log = logging.getLogger(__name__)


class ReleaseProvider(Provider):
    def __init__(self, database_url='https://cdn.rawgit.com/OpenEntityMap/', database_author='OpenEntityMap',
                 fmt='json', storage='file'):
        super(ReleaseProvider, self).__init__(storage)

        self.database_url = database_url
        self.database_author = database_author

        self._fmt = fmt
        self.format = None

    #
    # Public methods
    #

    def initialize(self, client):
        super(ReleaseProvider, self).initialize(client)

        # Construct format
        cls = PluginManager.get('format', self._fmt)

        if cls is None:
            raise ValueError('Unable to find format: %r' % self._fmt)

        self.format = cls()

    def open_database(self, source, target):
        # Ensure database has been created
        if not self.storage.create(source, target):
            return None

        # Update database
        self.update_database(source, target)

        # Open database
        return self.storage.open_database(source, target)

    #
    # Abstract methods
    #

    def update_database(self, source, target):
        raise NotImplementedError

    def get_available_version(self, source, target):
        raise NotImplementedError
