from plugin.core.environment import Environment

import os
import platform
import shutil
import sys
import tempfile


# Create dummy `Log`
try:
    Log.Debug('Using framework "Log" handler')
except NameError:
    from mock.framework import Logger

    Log = Logger()
    Log.Debug('Using dummy "Log" handler')

# Retrieve `contents_path`
code_path = Environment.path.code
contents_path = os.path.abspath(os.path.join(code_path, '..'))

# Constants/Maps
bits_map = {
    '32bit': 'i386',
    '64bit': 'x86_64'
}

machine_map = {
    ('32bit', 'i686'): 'i686'
}

system_map = {
    'Darwin': 'MacOSX'
}

unicode_map = {
    65535:      'ucs2',
    1114111:    'ucs4'
}

native_directories = [
    'Libraries\\FreeBSD',
    'Libraries\\Linux',
    'Libraries\\MacOSX',
    'Libraries\\Windows'
]

def get_architecture():
    bits, _ = platform.architecture()
    machine = platform.machine()

    # Check (bits, machine) map
    machine_key = (bits, machine)

    if machine_key in machine_map:
        return machine_map[machine_key]

    # Check (bits) map
    if bits in bits_map:
        return bits_map[bits]

    Log.Info('Unable to determine system architecture - bits: %r, machine: %r', bits, machine)
    return None


def get_system():
    system = platform.system()

    # Apply system map
    if system in system_map:
        system = system_map[system]

    return system

class Libraries(object):
    @classmethod
    def cache(cls):
        # Retrieve library platforms
        libraries_path = os.path.join(contents_path, 'Libraries')
        platforms = os.listdir(libraries_path)

        if 'Shared' in platforms:
            platforms.remove('Shared')

        # Create destination directory
        destination = os.path.join(Environment.path.plugin_data, 'Libraries')

        # Ensure destination exists
        cls.create_directories(destination)

        # Delete existing libraries
        for name in os.listdir(destination):
            path = os.path.join(destination, name)

            cls.delete_tree(path)

        # Copy libraries to directory
        for name in platforms:
            p_source = os.path.join(libraries_path, name)
            p_destination = os.path.join(destination, name)

            if not cls.copy_tree(p_source, p_destination):
                return None

        Log.Debug('Cached native libraries to %r', cls.relative_path(destination))
        return destination

    @classmethod
    def setup(cls, cache=False):
        # Retrieve libraries path
        libraries_path = Environment.path.libraries

        if cache:
            # Reset native library directories in `sys.path`
            cls.reset()

            # Cache native libraries
            libraries_path = cls.cache()

        Log.Info('Using native libraries at %r', cls.relative_path(libraries_path))

        # Retrieve system details
        system = get_system()
        system_architecture = get_architecture()

        if not system_architecture:
            return

        Log.Debug('System: %r, Architecture: %r', system, system_architecture)

        architectures = [system_architecture]

        if system_architecture == 'i686':
            # Fallback to i386
            architectures.append('i386')

        for architecture in reversed(architectures + ['universal']):
            # Common
            cls.insert_path(libraries_path, system, architecture)

            # UCS
            if sys.maxunicode in unicode_map:
                cls.insert_path(libraries_path, system, architecture, unicode_map[sys.maxunicode])

        # Log library paths
        for path in sys.path:
            path = os.path.abspath(path)
            path_lower = path.lower()

            if 'trakttv.bundle' not in path_lower and 'plug-in support' not in path_lower:
                continue

            Log.Debug('[PATH] %s', cls.relative_path(path))

    @classmethod
    def reset(cls):
        for path in sys.path:
            path = os.path.abspath(path)

            if not path.lower().startswith(contents_path.lower()):
                continue

            # Convert to relative path
            path_rel = os.path.relpath(path, contents_path)

            # Take the first two fragments
            path_rel = os.path.sep.join(path_rel.split(os.path.sep)[:2])

            # Ignore non-native library directories
            if path_rel not in native_directories:
                continue

            # Remove from `sys.path`
            cls.remove_path(path)

    @classmethod
    def insert_path(cls, base, system, architecture, *args):
        path = os.path.join(base, system, architecture, *args)

        if path in sys.path:
            return

        if not os.path.exists(path):
            return

        sys.path.insert(0, path)

        Log.Debug('Inserted path: %r', cls.relative_path(path))

    @classmethod
    def remove_path(cls, path):
        sys.path.remove(path)

        Log.Debug('Removed path: %r', cls.relative_path(path))

    @classmethod
    def create_directories(cls, path, *args, **kwargs):
        try:
            os.makedirs(path, *args, **kwargs)
            return True
        except OSError, ex:
            if ex.errno == 17:
                return False

            Log.Warn('Unable to create directories: %r - (%s) %s', cls.relative_path(path), ex.errno, ex)
        except Exception, ex:
            Log.Warn('Unable to create directories: %r - (%s) %s', cls.relative_path(path), type(ex), ex)

        return False

    @classmethod
    def copy_tree(cls, source, destination):
        try:
            shutil.copytree(source, destination)

            Log.Debug('Copied %r to %r', cls.relative_path(source), cls.relative_path(destination))
            return True
        except Exception, ex:
            Log.Warn('Unable to copy %r to %r - %s', cls.relative_path(source), cls.relative_path(destination), ex)

        return False

    @classmethod
    def delete_tree(cls, path):
        try:
            shutil.rmtree(path)

            Log.Debug('Deleted %r', cls.relative_path(path))
            return True
        except Exception, ex:
            Log.Warn('Unable to delete directory: %r - %s', cls.relative_path(path), ex)

        return False

    @staticmethod
    def relative_path(path):
        path_lower = path.lower()

        if 'plug-ins' in path_lower:
            base_path = path[:path_lower.find('plug-ins')]
        elif 'plug-in support' in path_lower:
            base_path = path[:path_lower.find('plug-in support')]
        elif 'trakttv.bundle' in path_lower:
            base_path = path[:path_lower.find('trakttv.bundle')]
        else:
            Log.Warn('Unable to find base path in %r', path)
            return path

        return os.path.relpath(path, base_path)
