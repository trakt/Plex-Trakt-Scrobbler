from plugin.core.environment import Environment
from plugin.core.helpers.variable import merge
from plugin.core.libraries.cache import CacheManager
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
    def setup(cls, cache=False):
        """Setup native library directories

        :param cache: Enable native library caching
        :type cache: bool
        """

        # Retrieve libraries path (and cache libraries, if enabled)
        libraries_path = cls._libraries_path(cache)

        log.info('Using native libraries at %r', StorageHelper.to_relative_path(libraries_path))

        # Insert platform specific library paths
        cls._insert_paths(libraries_path)

        # Display library paths in logfile
        for path in sys.path:
            path = os.path.abspath(path)

            if not StorageHelper.is_relative_path(path):
                continue

            log.info('[PATH] %s', StorageHelper.to_relative_path(path))

    @staticmethod
    def test():
        """Test native libraries to ensure they can be correctly loaded"""
        log.info('Testing native library support...')

        metadata = {}

        for test in LIBRARY_TESTS:
            # Run tests
            result = test.run()

            if not result.get('success'):
                # Write message to logfile
                log.error('%s: unavailable - %s', test.name, result.get('message'), exc_info=result.get('exc_info'))

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

    @classmethod
    def _libraries_path(cls, cache=False):
        """Retrieve the native libraries base directory (and cache the libraries if enabled)

        :param cache: Enable native library caching
        :type cache: bool
        """

        if not cache:
            return Environment.path.libraries

        # Cache native libraries
        libraries_path = CacheManager.sync()

        if libraries_path:
            # Reset native library directories in `sys.path`
            cls.reset()

            return libraries_path

        return Environment.path.libraries

    @classmethod
    def _insert_paths(cls, libraries_path):
        # Retrieve system details
        system = SystemHelper.name()
        architecture = SystemHelper.architecture()

        if not architecture:
            return

        log.debug('System: %r, Architecture: %r', system, architecture)

        # Insert architecture specific libraries
        architectures = [architecture]

        if architecture == 'i686':
            # Fallback to i386
            architectures.append('i386')

        for arch in reversed(architectures + ['universal']):
            cls._insert_architecture_paths(libraries_path, system, arch)

    @classmethod
    def _insert_architecture_paths(cls, libraries_path, system, architecture):
        architecture_path = os.path.join(libraries_path, system, architecture)

        if not os.path.exists(architecture_path):
            return

        # Architecture libraries
        PathHelper.insert(libraries_path, system, architecture)

        # System libraries
        if system == 'Windows':
            # Windows libraries (VC++ specific)
            cls._insert_paths_windows(libraries_path, system, architecture)
        else:
            # Darwin/FreeBSD/Linux libraries
            cls._insert_paths_unix(libraries_path, system, architecture)

    @staticmethod
    def _insert_paths_unix(libraries_path, system, architecture):
        ucs = UNICODE_MAP.get(sys.maxunicode)

        log.debug('UCS: %r', ucs)

        # UCS libraries
        if ucs:
            PathHelper.insert(libraries_path, system, architecture, ucs)

        # Include attributes in error reports
        RAVEN.tags.update({
            'python.ucs': ucs
        })

    @staticmethod
    def _insert_paths_windows(libraries_path, system, architecture):
        vcr = SystemHelper.vcr_version() or 'vc12'  # Assume "vc12" if call fails
        ucs = UNICODE_MAP.get(sys.maxunicode)

        log.debug('VC++ Runtime: %r, UCS: %r', vcr, ucs)

        # VC++ libraries
        PathHelper.insert(libraries_path, system, architecture, vcr)

        # UCS libraries
        if ucs:
            PathHelper.insert(libraries_path, system, architecture, vcr, ucs)

        # Include attributes in error reports
        RAVEN.tags.update({
            'python.ucs': ucs,
            'vcr.version': vcr
        })
