from plugin.core.environment import Environment
from plugin.core.libraries.helpers import PathHelper, StorageHelper, SystemHelper

import logging
import os
import sys

log = logging.getLogger(__name__)


class LibrariesManager(object):
    contents_path = os.path.abspath(os.path.join(Environment.path.code, '..'))

    native_directories = [
        'Libraries\\FreeBSD',
        'Libraries\\Linux',
        'Libraries\\MacOSX',
        'Libraries\\Windows'
    ]

    unicode_map = {
        65535:      'ucs2',
        1114111:    'ucs4'
    }

    @classmethod
    def cache(cls):
        """Cache native libraries into the plugin data directory"""

        # Retrieve library platforms
        libraries_path = os.path.join(cls.contents_path, 'Libraries')
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
            if sys.maxunicode in cls.unicode_map:
                PathHelper.insert(libraries_path, system, architecture, cls.unicode_map[sys.maxunicode])

        # Log library paths
        for path in sys.path:
            path = os.path.abspath(path)

            if not StorageHelper.is_relative_path(path):
                continue

            log.info('[PATH] %s', StorageHelper.to_relative_path(path))

    @staticmethod
    def test():
        log.info('Testing native library support...')

        # Check "apsw" availability
        try:
            import apsw

            log.info(' - apsw: available (v%s) [sqlite: %s]', apsw.apswversion(), apsw.SQLITE_VERSION_NUMBER)
        except Exception, ex:
            log.error(' - Unable to import "apsw": %s', ex)

        # Check "llist" availability
        try:
            import llist

            log.info(' - llist: available')
        except Exception, ex:
            log.warn(' - Unable to import "llist": %s', ex)

        # Check "lxml" availability
        try:
            import lxml

            log.info(' - lxml: available')
        except Exception, ex:
            log.warn(' - Unable to import "lxml": %s', ex)

        # Check "cryptography" availability
        cryptography_available = False

        try:
            import cryptography
            from cryptography.hazmat.bindings.openssl.binding import Binding

            cryptography_version = getattr(cryptography, '__version__', None)
            openssl_version = Binding.lib.SSLeay()

            log.info(' - cryptography: available (v%s) [openssl: %s]', cryptography_version, openssl_version)
            cryptography_available = True
        except Exception, ex:
            log.warn(' - Unable to import "cryptography": %s', ex)

        # Check "OpenSSL" availability
        openssl_available = False

        try:
            import OpenSSL

            log.info(' - pyopenssl: available (v%s)', getattr(OpenSSL, '__version__', None))
            openssl_available = True
        except Exception, ex:
            log.warn(' - Unable to import "pyopenssl": %s', ex)

        # Inject pyopenssl into requests/urllib3 (if supported)
        if cryptography_available and openssl_available:
            try:
                from requests.packages.urllib3.contrib.pyopenssl import inject_into_urllib3

                inject_into_urllib3()

                log.info(' - requests + pyopenssl: available')
            except Exception, ex:
                log.warn(' - Unable to inject "pyopenssl": %s', ex)

    @classmethod
    def reset(cls):
        """Remove all the native library directives from `sys.path`"""

        for path in sys.path:
            path = os.path.abspath(path)

            if not path.lower().startswith(cls.contents_path.lower()):
                continue

            # Convert to relative path
            path_rel = os.path.relpath(path, cls.contents_path)

            # Take the first two fragments
            path_rel = os.path.sep.join(path_rel.split(os.path.sep)[:2])

            # Ignore non-native library directories
            if path_rel not in cls.native_directories:
                continue

            # Remove from `sys.path`
            PathHelper.remove(path)
