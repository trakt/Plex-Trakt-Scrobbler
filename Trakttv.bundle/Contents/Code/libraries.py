from plugin.core.environment import Environment

import os
import platform
import sys

bits_map = {
    '32bit': 'i386',
    '64bit': 'x86_64'
}

machine_map = {
    ('32bit', 'i686'): 'i686'
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


def setup_libraries():
    system = platform.system()
    architecture = get_architecture()

    if not architecture:
        return

    Log.Debug('System: %r, Architecture: %r', system, architecture)

    if architecture == 'i686':
        insert_path(system, 'i386')

    insert_path(system, architecture)


def insert_path(system, architecture):
    path = os.path.join(Environment.path.libraries, system, architecture)

    if path in sys.path:
        return

    sys.path.insert(0, path)

    Log.Debug('Inserted path: %r (for compiled libraries)', path)
