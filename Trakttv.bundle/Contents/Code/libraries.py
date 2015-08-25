from plugin.core.environment import Environment

import os
import platform
import sys


# Retrieve `contents_path`
try:
    code_path = Core.code_path
except NameError:
    code_path = os.path.dirname(__file__)

contents_path = os.path.abspath(os.path.join(code_path, '..'))

# Create dummy `Log`
try:
    Log.Debug('Using framework "Log" handler')
except NameError:
    from mock.framework import Logger

    Log = Logger()
    Log.Debug('Using dummy "Log" handler')

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


def setup_libraries():
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
        insert_path(system, architecture)

        # UCS
        if sys.maxunicode in unicode_map:
            insert_path(system, architecture, unicode_map[sys.maxunicode])

    # Log library paths
    for path in sys.path:
        path = os.path.abspath(path)

        if not path.lower().startswith(contents_path.lower()):
            return

        path = os.path.relpath(path, contents_path)

        Log.Debug('[PATH] %s', path)


def insert_path(system, architecture, *args):
    path = os.path.join(Environment.path.libraries, system, architecture, *args)

    if path in sys.path:
        return

    if not os.path.exists(path):
        return

    sys.path.insert(0, path)

    Log.Debug('Inserted path: %r (for compiled libraries)', path)
