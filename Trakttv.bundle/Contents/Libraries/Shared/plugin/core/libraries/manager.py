from plugin.core.configuration import Configuration
from plugin.core.environment import Environment
from plugin.core.message import InterfaceMessages
from plugin.core.helpers.variable import merge
from plugin.core.libraries.cache import CacheManager
from plugin.core.libraries.constants import CONTENTS_PATH, NATIVE_DIRECTORIES, UNICODE_MAP
from plugin.core.libraries.helpers import PathHelper, StorageHelper, SystemHelper
from plugin.core.libraries.tests import LIBRARY_TESTS

import json
import logging
import os
import platform
import sys

log = logging.getLogger(__name__)


class LibrariesManager(object):
    @classmethod
    def setup(cls, cache=False):
        """Setup native library directories

        :param cache: Enable native library caching
        :type cache: bool
        """

        # Read distribution metadata
        distribution = cls._read_distribution_metadata()

        # Use `cache` value from advanced configuration
        cache = Configuration.advanced['libraries'].get_boolean('cache', cache)

        # Retrieve libraries path (and cache libraries, if enabled)
        libraries_path = cls._libraries_path(cache)

        if not libraries_path:
            return

        log.info('Using native libraries at %r', StorageHelper.to_relative_path(libraries_path))

        # Remove current native library directories from `sys.path`
        cls.reset()

        # Insert platform specific library paths
        cls._insert_paths(distribution, libraries_path)

        # Display library paths in logfile
        for path in sys.path:
            path = os.path.abspath(path)

            if StorageHelper.is_framework_path(path):
                continue

            log.info('[PATH] %s', StorageHelper.to_relative_path(path))

    @staticmethod
    def test():
        """Test native libraries to ensure they can be correctly loaded"""
        log.info('Testing native library support...')

        # Retrieve library directories
        search_paths = []

        for path in sys.path:
            path_lower = path.lower()

            if 'trakttv.bundle' not in path_lower and 'com.plexapp.plugins.trakttv' not in path_lower:
                continue

            search_paths.append(path)

        # Run library tests
        metadata = {}

        for test in LIBRARY_TESTS:
            # Run tests
            result = test.run(search_paths)

            if not result.get('success'):
                log_func = logging.warn if test.optional else logging.error

                # Write message to logfile
                if 'traceback' in result:
                    log_func('%s: unavailable - %s\n%%s' % (test.name, result.get('message')), result['traceback'])
                else:
                    log_func('%s: unavailable - %s' % (test.name, result.get('message')), exc_info=result.get('exc_info'))

                if not test.optional:
                    return

                continue

            # Test successful
            t_metadata = result.get('metadata') or {}
            t_versions = t_metadata.get('versions')

            if t_versions:
                expanded = len(t_versions) > 1 or (
                    t_versions and t_versions.keys()[0] != test.name
                )

                if expanded:
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

            # Convert to unix-style separators (/)
            path_rel = path_rel.replace('\\', '/')

            # Ignore non-native library directories
            if path_rel not in NATIVE_DIRECTORIES:
                continue

            # Remove from `sys.path`
            PathHelper.remove(path)

    @classmethod
    def _read_distribution_metadata(cls):
        metadata_path = os.path.join(Environment.path.contents, 'distribution.json')

        if not os.path.exists(metadata_path):
            return None

        # Read distribution metadata
        try:
            with open(metadata_path, 'r') as fp:
                distribution = json.load(fp)
        except Exception as ex:
            log.warn('Unable to read distribution metadata: %s', ex, exc_info=True)
            return None

        if not distribution or not distribution.get('name'):
            return

        return distribution

    @classmethod
    def _libraries_path(cls, cache=False):
        """Retrieve the native libraries base directory (and cache the libraries if enabled)

        :param cache: Enable native library caching
        :type cache: bool
        """

        # Use specified libraries path (from "advanced.ini')
        libraries_path = Configuration.advanced['libraries'].get('libraries_path')

        if libraries_path and os.path.exists(libraries_path):
            log.info('Using libraries at %r', StorageHelper.to_relative_path(libraries_path))
            return libraries_path

        # Use system libraries (if bundled libraries have been disabled in "advanced.ini")
        if not Configuration.advanced['libraries'].get_boolean('bundled', True):
            log.info('Bundled libraries have been disabled, using system libraries')
            return None

        # Cache libraries (if enabled)
        if cache:
            return cls._cache_libraries()

        return Environment.path.libraries

    @classmethod
    def _cache_libraries(cls):
        cache_path = Configuration.advanced['libraries'].get('cache_path')

        # Try cache libraries to `cache_path`
        libraries_path = CacheManager.sync(cache_path)

        if not libraries_path:
            log.info('Unable to cache libraries, using bundled libraries directly')
            return Environment.path.libraries

        log.info('Cached libraries to %r', StorageHelper.to_relative_path(libraries_path))
        return libraries_path

    @classmethod
    def _insert_paths(cls, distribution, libraries_path):
        # Display platform details
        p_bits, _ = platform.architecture()
        p_machine = platform.machine()

        log.debug('Bits: %r, Machine: %r', p_bits, p_machine)

        # Retrieve system details
        system = SystemHelper.name()
        architecture = SystemHelper.architecture()

        if not architecture:
            InterfaceMessages.add(60, 'Unable to retrieve system architecture')
            return False

        log.debug('System: %r, Architecture: %r', system, architecture)

        # Build architecture list
        architectures = [architecture]

        if architecture == 'i686':
            # Fallback to i386
            architectures.append('i386')

        # Insert library paths
        found = False

        for arch in architectures + ['universal']:
            if cls._insert_architecture_paths(libraries_path, system, arch):
                log.debug('Inserted libraries path for system: %r, arch: %r', system, arch)
                found = True

        # Display interface message if no libraries were found
        if not found:
            if distribution and distribution.get('name'):
                message = 'Unable to find compatible native libraries in the %s distribution' % distribution['name']
            else:
                message = 'Unable to find compatible native libraries'

            InterfaceMessages.add(60, '%s (system: %r, architecture: %r)', message, system, architecture)

        return found

    @classmethod
    def _insert_architecture_paths(cls, libraries_path, system, architecture):
        architecture_path = os.path.join(libraries_path, system, architecture)

        if not os.path.exists(architecture_path):
            return False

        # Architecture libraries
        PathHelper.insert(libraries_path, system, architecture)

        # System libraries
        if system == 'Windows':
            # Windows libraries (VC++ specific)
            cls._insert_paths_windows(libraries_path, system, architecture)
        else:
            # Darwin/FreeBSD/Linux libraries
            cls._insert_paths_unix(libraries_path, system, architecture)

        return True

    @staticmethod
    def _insert_paths_unix(libraries_path, system, architecture):
        # UCS specific libraries
        ucs = UNICODE_MAP.get(sys.maxunicode)
        log.debug('UCS: %r', ucs)

        if ucs:
            PathHelper.insert(libraries_path, system, architecture, ucs)

        # CPU specific libraries
        cpu_type = SystemHelper.cpu_type()
        page_size = SystemHelper.page_size()

        log.debug('CPU Type: %r', cpu_type)
        log.debug('Page Size: %r', page_size)

        if cpu_type:
            PathHelper.insert(libraries_path, system, architecture, cpu_type)

            if page_size:
                PathHelper.insert(libraries_path, system, architecture, '%s_%s' % (cpu_type, page_size))

        # UCS + CPU specific libraries
        if cpu_type and ucs:
            PathHelper.insert(libraries_path, system, architecture, cpu_type, ucs)

            if page_size:
                PathHelper.insert(libraries_path, system, architecture, '%s_%s' % (cpu_type, page_size), ucs)

    @staticmethod
    def _insert_paths_windows(libraries_path, system, architecture):
        vcr = SystemHelper.vcr_version() or 'vc12'  # Assume "vc12" if call fails
        ucs = UNICODE_MAP.get(sys.maxunicode)

        log.debug('VCR: %r, UCS: %r', vcr, ucs)

        # VC++ libraries
        PathHelper.insert(libraries_path, system, architecture, vcr)

        # UCS libraries
        if ucs:
            PathHelper.insert(libraries_path, system, architecture, vcr, ucs)
