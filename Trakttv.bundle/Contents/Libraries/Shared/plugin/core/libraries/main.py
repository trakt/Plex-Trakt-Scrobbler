from plugin.core.environment import Environment
from plugin.core.helpers.variable import merge
from plugin.core.libraries.constants import CONTENTS_PATH, NATIVE_DIRECTORIES, UNICODE_MAP
from plugin.core.libraries.helpers import PathHelper, StorageHelper, SystemHelper
from plugin.core.libraries.tests import LIBRARY_TESTS
from plugin.core.logger.handlers.error_reporter import RAVEN

import logging
import os
import sys

log = logging.getLogger(__name__)


class LibrariesManager(object):
    @classmethod
    def cache(cls):
        """Cache native libraries into the plugin data directory"""

        # Retrieve library platforms
        libraries_path = os.path.join(CONTENTS_PATH, 'Libraries')
        platforms = os.listdir(libraries_path)

        if 'Shared' in platforms:
            platforms.remove('Shared')

        # Create destination directory
        destination = os.path.join(Environment.path.plugin_data, 'Libraries')

        # Ensure destination exists
        StorageHelper.create_directories(destination)

        # Delete existing libraries
        for name in os.listdir(destination):
            path = os.path.join(destination, name)

            StorageHelper.delete_tree(path)

        # Copy libraries to directory
        for name in platforms:
            p_source = os.path.join(libraries_path, name)
            p_destination = os.path.join(destination, name)

            if not StorageHelper.copy_tree(p_source, p_destination):
                return None

        log.debug('Cached native libraries to %r', StorageHelper.to_relative_path(destination))
        return destination

    @classmethod
    def get_libraries_path(cls, cache=False):
        """Retrieve the native libraries base directory (and caching the libraries if enabled)"""

        if not cache:
            return Environment.path.libraries

        # Cache native libraries
        libraries_path = cls.cache()

        if libraries_path:
            # Reset native library directories in `sys.path`
            cls.reset()

            return libraries_path

        return Environment.path.libraries

    @classmethod
    def setup(cls, cache=False):
        """Setup native library directories"""

        # Retrieve libraries path
        libraries_path = cls.get_libraries_path(cache)

        log.info('Using native libraries at %r', StorageHelper.to_relative_path(libraries_path))

        # Retrieve system details
        system = SystemHelper.name()
        system_architecture = SystemHelper.architecture()

        if not system_architecture:
            return

        log.debug('System: %r, Architecture: %r', system, system_architecture)

        architectures = [system_architecture]

        if system_architecture == 'i686':
            # Fallback to i386
            architectures.append('i386')

        for architecture in reversed(architectures + ['universal']):
            # Common
            PathHelper.insert(libraries_path, system, architecture)

            # UCS
            if sys.maxunicode in UNICODE_MAP:
                PathHelper.insert(libraries_path, system, architecture, UNICODE_MAP[sys.maxunicode])

        # Log library paths
        for path in sys.path:
            path = os.path.abspath(path)

            if not StorageHelper.is_relative_path(path):
                continue

            log.info('[PATH] %s', StorageHelper.to_relative_path(path))

    @staticmethod
    def test():
        log.info('Testing native library support...')

        metadata = {}

        for test in LIBRARY_TESTS:
            # Run tests
            result = test.run()

            if not result.get('success'):
                # Format error message
                message = '%s: unavailable - %s' % (test.name, result.get('message'))

                # Write message to logfile
                log.error(message, exc_info=result.get('exc_info'))

                if not test.optional:
                    return

                continue

            # Test successful
            t_metadata = result.get('metadata') or {}
            t_versions = t_metadata.get('versions')

            if t_versions:
                if len(t_versions) > 1:
                    log.info('%s: available (%s)', test.name, ', '.join([
                        '%s: %s' % (key, value)
                        for key, value in t_versions.items()
                    ]))
                else:
                    key = t_versions.keys()[0]

                    log.info('%s: available (%s)', test.name, t_versions[key])
            else:
                log.info('%s: available', test.name)

            # Merge result into `metadata`
            merge(metadata, t_metadata, recursive=True)

        # Include versions in error reports
        versions = metadata.get('versions') or {}

        RAVEN.tags.update(dict([
            ('%s.version' % key, value)
            for key, value in versions.items()
        ]))

    @classmethod
    def reset(cls):
        """Remove all the native library directives from `sys.path`"""

        for path in sys.path:
            path = os.path.abspath(path)

            if not path.lower().startswith(CONTENTS_PATH.lower()):
                continue

            # Convert to relative path
            path_rel = os.path.relpath(path, CONTENTS_PATH)

            # Take the first two fragments
            path_rel = os.path.sep.join(path_rel.split(os.path.sep)[:2])

            # Ignore non-native library directories
            if path_rel not in NATIVE_DIRECTORIES:
                continue

            # Remove from `sys.path`
            PathHelper.remove(path)
