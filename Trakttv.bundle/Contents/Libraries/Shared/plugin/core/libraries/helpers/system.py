from elftools.elf.attributes import AttributesSection
from elftools.elf.elffile import ELFFile
import logging
import os
import platform
import sys

log = logging.getLogger(__name__)

BITS_MAP = {
    '32bit': 'i386',
    '64bit': 'x86_64'
}

MACHINE_MAP = {
    ('32bit', 'i686'): 'i686'
}

MSVCR_MAP = {
    'msvcr120.dll': 'vc12',
    'msvcr130.dll': 'vc14'
}

NAME_MAP = {
    'Darwin': 'MacOSX'
}


class SystemHelper(object):
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

        if machine_key in MACHINE_MAP:
            return MACHINE_MAP[machine_key]

        # Check (bits) map
        if bits in BITS_MAP:
            return BITS_MAP[bits]

        log.error('Unable to determine system architecture - bits: %r, machine: %r', bits, machine)
        return None

    @classmethod
    def name(cls):
        """Retrieve system name (Windows, Linux, FreeBSD, MacOSX)"""

        system = platform.system()

        # Apply system map
        if system in NAME_MAP:
            system = NAME_MAP[system]

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
    def arm_float_type(cls, executable_path=sys.executable):
        if os.path.exists('/lib/arm-linux-gnueabihf'):
            return 'hf'

        if os.path.exists('/lib/arm-linux-gnueabi'):
            return 'sf'

        # Determine system float-type from python executable
        section, attributes = cls.elf_attributes(executable_path)

        if not section or not attributes:
            return None

        if section.name != 'aeabi':
            log.warn('Unknown attributes section name: %r', section.name)
            return None

        # Assume hard-float if "tag_abi_vfp_args" is present
        if attributes.get('abi_vfp_args'):
            return 'hf'

        return 'sf'

    @classmethod
    def elf_attributes(cls, executable_path=sys.executable):
        try:
            # Open executable stream
            stream = open(executable_path, 'rb')

            # Parse ELF
            elf = ELFFile(stream)

            # Find attributes section
            section = cls._find_elf_section(elf, AttributesSection)

            if section is None:
                log.warn('Unable to find attributes section in ELF: %r', executable_path)
                return None, None

            # Build dictionary of attributes
            attributes = dict([
                (attr.tag.lower(), attr.value)
                for attr in section.iter_attributes()
            ])

            return section, attributes
        except Exception, ex:
            log.warn('Unable to retrieve attributes from ELF %r: %s', executable_path, ex, exc_info=True)

        return None, None

    @staticmethod
    def _find_elf_section(elf, cls):
        for section in elf.iter_sections():
            if isinstance(section, cls):
                return section

        return None

    @classmethod
    def vcr_version(cls):
        try:
            import ctypes.util

            # Retrieve linked msvcr dll
            name = ctypes.util.find_msvcrt()

            # Return VC++ version from map
            if name not in MSVCR_MAP:
                log.error('Unknown VC++ runtime: %r', name)
                return None

            return MSVCR_MAP[name]
        except Exception:
            log.error('Unable to retrieve VC++ runtime version', exc_info=True)
            return None
