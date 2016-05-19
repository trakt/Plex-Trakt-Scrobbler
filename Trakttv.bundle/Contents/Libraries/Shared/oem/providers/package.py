from oem.providers.core.base import Provider

import logging
import os
import sys

log = logging.getLogger(__name__)


class PackageProvider(Provider):
    __key__ = 'package'

    def __init__(self, search_paths=None, use_installed_packages=True, storage='file'):
        super(PackageProvider, self).__init__(storage)

        self.search_paths = search_paths or []
        self.use_installed_packages = use_installed_packages

        self.format = None

    def initialize(self, client):
        super(PackageProvider, self).initialize(client)

        self._storage.path = None

    #
    # Public methods
    #

    def fetch(self, source, target, key, metadata):
        return True

    def open_database(self, source, target):
        # Find database package
        database_path = self._find_database(source, target)

        if database_path is None:
            return None

        # Pick collection format
        self.format = self._pick_format(database_path, source)

        if self.format is None:
            return None

        # Open database
        return self.storage.open_database(
            source, target,
            path=database_path
        )

    def _find_database(self, source, target):
        names = [
            'oem_database_%s_%s' % (source, target),
            'oem_database_%s_%s' % (target, source)
        ]

        paths = [os.curdir] + self.search_paths

        if self.use_installed_packages:
            paths.extend(sys.path)

        for package_path in paths:
            # Ignore invalid paths
            if package_path.endswith('.egg') or package_path.endswith('.zip'):
                continue

            if not os.path.exists(package_path):
                continue

            # List items in `package_path`
            try:
                items = os.listdir(package_path)
            except Exception, ex:
                log.debug('Unable to list directory %r - %s', package_path, ex, exc_info=True)
                continue

            # Try find matching name in directory `items`
            for name in names:
                if name in items:
                    # Found database installation location
                    return os.path.join(package_path, name)

        # Unable to find database installation
        log.info('Unable to find database installation for: %s -> %s', source, target)
        return None

    def _pick_format(self, database_path, source):
        collection_path = os.path.join(database_path, source)

        # Retrieve available index formats
        names = os.listdir(collection_path)
        available = []

        for filename in names:
            if not filename.startswith('index.'):
                continue

            path = os.path.join(collection_path, filename)
            name, ext = os.path.splitext(filename)

            # Check for "msgpack" support
            if ext == 'mpack':
                # TODO ensure "msgpack" is available
                pass

            # Retrieve file modified date
            modified_date = os.path.getmtime(path)

            # Retrieve extension
            filename = os.path.basename(path)
            extension = filename.split('.', 1)[1]

            # Skip over ignored formats
            if self.formats is not None and extension not in self.formats:
                continue

            # Store index in `available` list
            available.append((modified_date, filename, extension))

        if len(available) < 1:
            raise Exception('No supported index available in %r' % collection_path)

        # Sort `available` by modified date
        available.sort(key=lambda i: i[0])

        # Use most recently modified index
        _, filename, extension = available[-1]

        # Find matching format
        for _, fmt in self.plugins.list_ordered('format'):
            if fmt.__extension__ == extension:
                return fmt()

        return None
