from oem.providers.core.base import Provider

from semantic_version import Version
import json
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
            log.warn('Unable to find database for: %s -> %s', source, target)
            return None

        # Pick collection format
        self.format = self._pick_format(database_path, source)

        if self.format is None:
            log.warn('Unable to find supported format in %r', database_path)
            return None

        # Open database
        return self.storage.open_database(
            source, target,
            path=database_path
        )

    def _find_database(self, source, target):
        identifiers = [
            (source, target),
            (target, source)
        ]

        paths = [os.curdir]

        if self.search_paths:
            paths.extend(self.search_paths)

        if self.use_installed_packages:
            paths.extend(sys.path)

        # Find database installation candidates
        candidates = []

        for package_path in paths:
            # Ignore invalid paths
            if package_path.endswith('.egg') or package_path.endswith('.zip'):
                continue

            if not os.path.exists(package_path):
                continue

            # List items in `package_path`
            try:
                items = os.listdir(package_path)
            except Exception as ex:
                log.debug('Unable to list directory %r - %s', package_path, ex, exc_info=True)
                continue

            # Try find matching name in directory `items`
            for name in items:
                path = os.path.abspath(os.path.join(package_path, name))

                # Check for valid database name
                if not self._is_database_name(path, name):
                    continue

                # Parse database name
                n_source, n_target, n_format = self._parse_database_name(name, identifiers)

                if not n_source or not n_target:
                    # Invalid database name
                    continue

                # Read package details
                details_path = os.path.join(path, 'package.json')

                if os.path.exists(details_path):
                    with open(details_path, 'r') as fp:
                        details = json.load(fp)

                    version = Version(details['version'])
                else:
                    version = None

                # Add installation candidate
                candidates.append((version, os.path.getmtime(path), path))

        if candidates:
            # Sort database candidates
            self._sort_candidates(candidates)

            # Select latest installation candidate
            _, _, path = candidates[0]
            return path

        # Unable to find database installation
        log.info('Unable to find database installation for: %s -> %s', source, target)
        return None

    @staticmethod
    def _is_database_name(path, name):
        if not name.startswith('oem_database'):
            return False

        if os.path.isfile(path):
            return False

        return True

    def _parse_database_name(self, name, identifiers):
        parts = name.split('_', 4)

        # Parse parts
        d_source = None
        d_target = None
        d_format = None

        if len(parts) >= 4:
            d_source = parts[2]
            d_target = parts[3]

        if len(parts) >= 5:
            d_format = parts[4]

        # Ensure name is valid
        if not d_source or not d_target:
            return None, None, None

        # Ensure database matches source + target
        if (d_source, d_target) not in identifiers:
            return None, None, None

        # Ensure format is valid
        if d_format and not self._is_database_format(d_format):
            return None, None, None

        return d_source, d_target, d_format

    def _is_database_format(self, extension):
        if not extension:
            return False

        extension = extension.replace('_', '.')

        # Check if format is installed
        for _, fmt in self.plugins.list('format'):
            if fmt.__extension__ == extension:
                return True

        return False

    @staticmethod
    def _sort_candidates(candidates):
        def sort_key(item):
            version, timestamp, path = item

            # Calculate order
            order = 0

            if version is None:
                order -= 2

            if timestamp is None:
                order -= 1

            # Return item sort key
            return order, version, timestamp, path

        candidates.sort(key=sort_key, reverse=True)

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
