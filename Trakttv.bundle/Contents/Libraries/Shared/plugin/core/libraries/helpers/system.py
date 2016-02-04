import logging
import os
import platform

log = logging.getLogger(__name__)


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

        log.info('Unable to determine system architecture - bits: %r, machine: %r', bits, machine)
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
            log.warn('Unable to use ARM libraries, unsupported floating-point type?')
            return None

        # Determine ARM version
        version = cls.arm_version()

        if version is None:
            log.warn('Unable to use ARM libraries, unsupported ARM version (%r)?' % machine)
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
