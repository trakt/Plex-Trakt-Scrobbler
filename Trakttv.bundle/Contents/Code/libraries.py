from plugin.core.environment import Environment

import os
import platform
import shutil
import sys


# Create dummy `Log` (for tests)
try:
    Log.Debug('Using framework "Log" handler')
except NameError:
    from plex_mock.framework import Logger

    Log = Logger()
    Log.Debug('Using dummy "Log" handler')


class Libraries(object):
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

        Log.Debug('Cached native libraries to %r', StorageHelper.to_relative_path(destination))
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

        Log.Info('Using native libraries at %r', StorageHelper.to_relative_path(libraries_path))

        # Retrieve system details
        system = SystemHelper.name()
        system_architecture = SystemHelper.architecture()

        if not system_architecture:
            return

        Log.Debug('System: %r, Architecture: %r', system, system_architecture)

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

            Log.Info('[PATH] %s', StorageHelper.to_relative_path(path))

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


class PathHelper(object):
    @classmethod
    def insert(cls, base, system, architecture, *args):
        """Insert a new path into `sys.path` if it passes basic validation"""

        path = os.path.join(base, system, architecture, *args)

        if path in sys.path:
            return False

        if not os.path.exists(path):
            return False

        sys.path.insert(0, path)

        Log.Debug('Inserted path: %r', StorageHelper.to_relative_path(path))
        return True

    @classmethod
    def remove(cls, path):
        """Remove path from `sys.path` if it exists"""

        if path not in sys.path:
            return False

        sys.path.remove(path)

        Log.Debug('Removed path: %r', StorageHelper.to_relative_path(path))
        return True


class StorageHelper(object):
    base_names = [
        'plug-ins',
        'plug-in support',
        'trakttv.bundle'
    ]

    @classmethod
    def create_directories(cls, path, *args, **kwargs):
        """Create directory at `path` include any parent directories"""

        try:
            os.makedirs(path, *args, **kwargs)
            return True
        except OSError, ex:
            if ex.errno == 17:
                # Directory already exists
                return True

            Log.Warn('Unable to create directories: %r - (%s) %s', cls.to_relative_path(path), ex.errno, ex)
        except Exception, ex:
            Log.Warn('Unable to create directories: %r - (%s) %s', cls.to_relative_path(path), type(ex), ex)

        return False

    @classmethod
    def copy_tree(cls, source, destination):
        """Copy the directory at `source` to `destination`"""

        try:
            shutil.copytree(source, destination)

            Log.Debug('Copied %r to %r', cls.to_relative_path(source), cls.to_relative_path(destination))
            return True
        except Exception, ex:
            Log.Warn('Unable to copy %r to %r - %s', cls.to_relative_path(source), cls.to_relative_path(destination), ex)

        return False

    @classmethod
    def delete_tree(cls, path):
        """Delete the directory (at `path`"""

        try:
            shutil.rmtree(path)

            Log.Debug('Deleted %r', cls.to_relative_path(path))
            return True
        except Exception, ex:
            Log.Warn('Unable to delete directory: %r - %s', cls.to_relative_path(path), ex)

        return False

    @classmethod
    def to_relative_path(cls, path):
        """Convert `path` to be relative to `StorageHelper.base_names`"""

        path_lower = path.lower()

        # Find base path
        base_path = None

        for base in cls.base_names:
            if base not in path_lower:
                continue

            base_path = path[:path_lower.find(base)]
            break

        # Check if `base_path` was found
        if not base_path:
            Log.Warn('Unable to find base path in %r', path)
            return path

        # Return relative path
        return os.path.relpath(path, base_path)

    @classmethod
    def is_relative_path(cls, path):
        """Check if `path` is relative to `StorageHelper.base_names`"""

        path_lower = path.lower()

        # Ignore framework paths
        if 'framework.bundle' in path_lower:
            return False

        # Find base path
        for base in cls.base_names:
            if base not in path_lower:
                continue

            return True

        return False


class SystemHelper(object):
    bits_map = {
        '32bit': 'i386',
        '64bit': 'x86_64'
    }

    machine_map = {
        ('32bit', 'i686'): 'i686'
    }

    name_map = {
        'Darwin': 'MacOSX'
    }

    @classmethod
    def architecture(cls):
        """Retrieve system architecture (i386, i686, x86_64)"""

        bits, _ = platform.architecture()
        machine = platform.machine()

        # Check for ARM machine
        if bits == '32bit' and machine.startswith('armv'):
            return cls.arm(machine)

        # Check (bits, machine) map
        machine_key = (bits, machine)

        if machine_key in cls.machine_map:
            return cls.machine_map[machine_key]

        # Check (bits) map
        if bits in cls.bits_map:
            return cls.bits_map[bits]

        Log.Info('Unable to determine system architecture - bits: %r, machine: %r', bits, machine)
        return None

    @classmethod
    def name(cls):
        """Retrieve system name (Windows, Linux, FreeBSD, MacOSX)"""

        system = platform.system()

        # Apply system map
        if system in cls.name_map:
            system = cls.name_map[system]

        return system

    @classmethod
    def arm(cls, machine):
        # Determine floating-point type
        float_type = cls.arm_float_type()

        if float_type is None:
            Log.Warn('Unable to use ARM libraries, unsupported floating-point type?')
            return None

        # Determine ARM version
        version = cls.arm_version()

        if version is None:
            Log.Warn('Unable to use ARM libraries, unsupported ARM version (%r)?' % machine)
            return None

        return '%s_%s' % (version, float_type)

    @classmethod
    def arm_version(cls, machine=None):
        # Read `machine` name if not provided
        if machine is None:
            machine = platform.machine()

        # Ensure `machine` is valid
        if not machine:
            return None

        # ARMv6
        if machine.startswith('armv6'):
            return 'armv6'

        # ARMv7
        if machine.startswith('armv7'):
            return 'armv7'

        return None

    @classmethod
    def arm_float_type(cls):
        if os.path.exists('/lib/arm-linux-gnueabihf'):
            return 'hf'

        if os.path.exists('/lib/arm-linux-gnueabi'):
            return 'sf'

        return None
