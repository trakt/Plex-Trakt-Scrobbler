from plugin.core.configuration import Configuration
from plugin.core.libraries.helpers.android import AndroidHelper
from plugin.core.libraries.helpers.arm import ArmHelper

from elftools.elf.attributes import AttributesSection
from elftools.elf.elffile import ELFFile
import logging
import os
import platform
import re
import sys

log = logging.getLogger(__name__)

_distributor_id_file_re = re.compile("(?:DISTRIB_ID\s*=)\s*(.*)", re.I)
_release_file_re = re.compile("(?:DISTRIB_RELEASE\s*=)\s*(.*)", re.I)
_codename_file_re = re.compile("(?:DISTRIB_CODENAME\s*=)\s*(.*)", re.I)

BITS_MAP = {
    '32bit': 'i386',
    '64bit': 'x86_64'
}

MACHINE_MAP = {
    ('32bit', 'i686'):  'i686',
    ('32bit', 'ppc' ):  'PowerPC'
}

MSVCR_MAP = {
    'msvcr110.dll': 'vc11',
    'msvcr120.dll': 'vc12',
    'msvcr130.dll': 'vc14'
}

NAME_MAP = {
    'Darwin': 'MacOSX'
}

FALLBACK_EXECUTABLE = '/bin/ls'


class SystemHelper(object):
    @classmethod
    def name(cls):
        """Retrieve system name (Windows, Linux, FreeBSD, MacOSX)"""

        system = platform.system()

        # Check for android platform
        if system == 'Linux' and AndroidHelper.is_android():
            system = 'Android'

        # Apply system name map
        if system in NAME_MAP:
            system = NAME_MAP[system]

        return system

    @classmethod
    def attributes(cls):
        # Retrieve platform attributes
        system = cls.name()

        release = platform.release()
        version = platform.version()

        # Build attributes dictionary
        result = {
            'cpu.architecture': cls.architecture(),
            'cpu.name': cls.cpu_name(),

            'os.system': system,

            'os.name': system,
            'os.release': release,
            'os.version': version
        }

        if system == 'Linux':
            # Update with linux distribution attributes
            result.update(cls.attributes_linux(
                release, version
            ))

        return result

    @classmethod
    def attributes_linux(cls, release=None, version=None):
        d_name, d_version, d_id = cls.distribution()

        # Build linux attributes dictionary
        result = {
            'os.name': None,
            'os.release': None,
            'os.version': None,

            'linux.release': release,
            'linux.version': version
        }
        
        if d_name:
            result['os.name'] = d_name

        if d_version:
            result['os.version'] = d_version

        if d_id:
            result['os.release'] = d_id

        return result

    @classmethod
    def architecture(cls):
        """Retrieve system architecture (i386, i686, x86_64)"""

        # Use `cpu_architecture` value from advanced configuration (if defined)
        cpu_architecture = Configuration.advanced['libraries'].get('cpu_architecture')

        if cpu_architecture:
            log.info('Using CPU Architecture from advanced configuration: %r', cpu_architecture)
            return cpu_architecture

        # Determine architecture from platform attributes
        bits, _ = platform.architecture()
        machine = platform.machine()

        # Check for ARM machine
        if (bits == '32bit' and machine.startswith('armv')) or machine.startswith('aarch64'):
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
    def arm(cls, machine, float_type=None):
        # Determine ARM version
        floats, architecture = cls.arm_architecture(machine)

        if architecture is None:
            log.warn('Unable to use ARM libraries, unsupported ARM architecture (%r)?' % machine)
            return None

        if not floats:
            return architecture

        # Determine floating-point type
        float_type = float_type or cls.arm_float_type()

        if float_type is None:
            log.warn('Unable to use ARM libraries, unsupported floating-point type?')
            return None

        return '%s_%s' % (architecture, float_type)

    @classmethod
    def arm_architecture(cls, machine=None):
        # Read `machine` name if not provided
        if machine is None:
            machine = platform.machine()

        # Ensure `machine` is valid
        if not machine:
            return False, None

        # ARMv5
        if machine.startswith('armv5'):
            return True, 'armv5'

        # ARMv6
        if machine.startswith('armv6'):
            return True, 'armv6'

        # ARMv7
        if machine.startswith('armv7'):
            return True, 'armv7'

        # ARMv8 / AArch64
        if machine.startswith('armv8') or machine.startswith('aarch64'):
            return False, 'aarch64'

        return False, None

    @classmethod
    def arm_float_type(cls, executable_path=sys.executable):
        # Use `arm_float_type` value from advanced configuration (if defined)
        arm_float_type = Configuration.advanced['libraries'].get('arm_float_type')

        if arm_float_type:
            log.info('Using ARM Float Type from advanced configuration: %r', arm_float_type)
            return arm_float_type

        # Try determine float-type from "/lib" directories
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
    def cpu_name(cls, executable_path=sys.executable):
        if cls.name() == 'Windows':
            return None

        # Retrieve CPU name from ELF
        section, attributes = cls.elf_attributes(executable_path)

        if not section or not attributes:
            return None

        name = attributes.get('cpu_name')

        if not name:
            return None

        return name.lower()

    @classmethod
    def cpu_type(cls, executable_path=sys.executable):
        # Use `cpu_type` value from advanced configuration (if defined)
        cpu_type = Configuration.advanced['libraries'].get('cpu_type')

        if cpu_type:
            log.info('Using CPU Type from advanced configuration: %r', cpu_type)
            return cpu_type

        # Try retrieve cpu type via "/proc/cpuinfo"
        try:
            _, _, cpu_type = ArmHelper.identifier()

            if cpu_type:
                return cpu_type
        except Exception as ex:
            log.warn('Unable to retrieve cpu type from "/proc/cpuinfo": %s', ex, exc_info=True)

        # Fallback to using the ELF cpu name
        return cls.cpu_name(executable_path)

    @classmethod
    def distribution(cls, distname='', version='', id='',
                     supported_dists=platform._supported_dists,
                     full_distribution_name=1):

        # check for the Debian/Ubuntu /etc/lsb-release file first, needed so
        # that the distribution doesn't get identified as Debian.
        try:
            _distname = None
            _version = None
            _id = None

            with open("/etc/lsb-release", "rU") as fp:
                for line in fp:
                    # Distribution Name
                    m = _distributor_id_file_re.search(line)

                    if m:
                        _distname = m.group(1).strip()

                    # Release
                    m = _release_file_re.search(line)

                    if m:
                        _version = m.group(1).strip()

                    # ID
                    m = _codename_file_re.search(line)

                    if m:
                        _id = m.group(1).strip()

                if _distname and _version:
                    return _distname, _version, _id

        except (EnvironmentError, UnboundLocalError):
            pass

        # Fallback to using the "platform" module
        return platform.linux_distribution(
            distname, version, id,
            supported_dists=supported_dists,
            full_distribution_name=full_distribution_name
        )

    @classmethod
    def elf_attributes(cls, executable_path=sys.executable):
        if cls.name() == 'MacOSX':
            log.info('Unable to retrieve ELF attributes on Mac OSX (not supported)')
            return None, None

        # Read attributes from "/bin/ls" if `executable_path` doesn't exist
        if not executable_path or not os.path.exists(executable_path):
            log.info('Executable at %r doesn\'t exist, using %r instead', executable_path, FALLBACK_EXECUTABLE)
            executable_path = FALLBACK_EXECUTABLE

        try:
            # Open executable stream
            stream = open(executable_path, 'rb')

            # Retrieve magic number (header)
            magic = stream.read(4)

            if magic != b'\x7fELF':
                log.warn('Unknown ELF format for %r (magic: %r)', executable_path, magic)
                return None, None

            stream.seek(0)

            # Parse ELF
            elf = ELFFile(stream)

            # Find attributes section
            section = cls._find_elf_section(elf, AttributesSection)

            if section is None:
                log.info('Unable to find attributes section in ELF: %r', executable_path)
                return None, None

            # Build dictionary of attributes
            attributes = dict([
                (attr.tag.lower(), attr.value)
                for attr in section.iter_attributes()
            ])

            return section, attributes
        except Exception as ex:
            log.warn('Unable to retrieve attributes from ELF %r: %s', executable_path, ex, exc_info=True)

        return None, None

    @classmethod
    def page_size(cls):
        try:
            import resource
            page_size = resource.getpagesize()

            if not page_size:
                return None

            return '%dk' % (page_size / 1024)
        except Exception as ex:
            log.warn('Unable to retrieve memory page size: %s', ex, exc_info=True)
            return None

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
