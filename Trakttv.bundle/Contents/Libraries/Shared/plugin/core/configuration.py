from plugin.core.environment import Environment

from ConfigParser import NoOptionError, NoSectionError, ParsingError, SafeConfigParser
import logging
import os

log = logging.getLogger(__name__)

CONFIGURATION_FILES = [
    'advanced'
]


class ConfigurationFile(object):
    def __init__(self, path):
        self._path = path
        self._relpath = os.path.relpath(self._path, Environment.path.plugin_support)

        self._parser = None
        self._error = False

    def __getitem__(self, section):
        # Ensure file is loaded
        self.load()

        # Construct section
        return ConfigurationSection(self._parser, section)

    def load(self):
        if self._parser or self._error:
            return

        log.debug('Parsing configuration file: %r', self._relpath)

        try:
            self._parser = SafeConfigParser()
            self._parser.read(self._path)
        except ParsingError as ex:
            log.info(ex.message)

            self._parser = None
            self._error = True
        except Exception as ex:
            log.warn('Unable to parse configuration file: %r - %s', self._relpath, ex, exc_info=True)

            self._parser = None
            self._error = True


class ConfigurationSection(object):
    def __init__(self, parser, name):
        self._parser = parser
        self._name = name

    def _get(self, func, key, default=None):
        if not self._parser:
            return default

        if not self._parser.has_option(self._name, key):
            return default

        try:
            return getattr(self._parser, func)(self._name, key)
        except (NoSectionError, NoOptionError):
            return default

    def get(self, key, default=None):
        return self._get('get', key, default)

    def get_int(self, key, default=None):
        return self._get('getint', key, default)

    def get_float(self, key, default=None):
        return self._get('getfloat', key, default)

    def get_boolean(self, key, default=None):
        return self._get('getboolean', key, default)

    def __getitem__(self, key):
        if not self._parser:
            return None

        return self._parser.get(self._name, key)

    def __setitem__(self, key, value):
        if not self._parser:
            return

        self._parser.set(self._name, key, value)


class ConfigurationMeta(type):
    def __new__(cls, name, parents, dct):
        # Load configuration files
        for name in CONFIGURATION_FILES:
            # Build path
            path = os.path.join(Environment.path.plugin_data, '%s.ini' % name)

            # Parse configuration file
            dct[name] = ConfigurationFile(path)

        # Construct object
        return super(ConfigurationMeta, cls).__new__(cls, name, parents, dct)


class Configuration(object):
    __metaclass__ = ConfigurationMeta

    advanced = None
