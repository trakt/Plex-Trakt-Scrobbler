from plugin.core.constants import PLUGIN_IDENTIFIER

import gettext
import locale
import logging
import os
import platform

log = logging.getLogger(__name__)


class PathEnvironment(object):
    # TODO confirm validity of this on *nix and OS X

    def __init__(self, core):
        self._core = core

        self._plugin_support = None

    @property
    def contents(self):
        return os.path.abspath(os.path.join(self.code, '..'))

    @property
    def code(self):
        return self._core.code_path

    @property
    def libraries(self):
        return os.path.join(self.contents, 'Libraries')

    @property
    def locale(self):
        return os.path.join(self.contents, 'Locale')

    @property
    def plugin_caches(self):
        return os.path.join(self.plugin_support, 'Caches', PLUGIN_IDENTIFIER)

    @property
    def plugin_data(self):
        return os.path.join(self.plugin_support, 'Data', PLUGIN_IDENTIFIER)

    @property
    def plugin_database(self):
        return os.path.join(self.plugin_support, 'Databases', '%s.db' % PLUGIN_IDENTIFIER)

    @property
    def plugin_support(self):
        if self._plugin_support is not None:
            return self._plugin_support

        base_path = self.code[:self.code.index(os.path.sep + 'Plug-ins')]

        return os.path.join(base_path, 'Plug-in Support')

    @plugin_support.setter
    def plugin_support(self, path):
        self._plugin_support = path


class PlatformEnvironment(object):
    def __init__(self, platform):
        self._platform = platform

    @property
    def machine_identifier(self):
        return self._platform.MachineIdentifier

    @property
    def server_version(self):
        return self._platform.ServerVersion


class Environment(object):
    dict = None
    path = None
    platform = None
    prefs = None

    language = None
    translation = None

    @classmethod
    def setup(cls, core, dict, platform, prefs):
        cls.path = PathEnvironment(core)
        cls.dict = dict
        cls.platform = PlatformEnvironment(platform)
        cls.prefs = prefs

    @classmethod
    def setup_locale(cls):
        # Setup locale
        try:
            locale.setlocale(locale.LC_ALL, '')
        except Exception, ex:
            log.warn('Unable to set locale: %s', ex, exc_info=True)
            return False

        log.info('Using locale: %r', locale.getlocale())
        return True

    @classmethod
    def setup_translation(cls):
        # Determine preferred language
        if platform.system() == 'Windows':
            cls.language = cls._get_windows_locale()
        else:
            cls.language = locale.getdefaultlocale()[0]

        if not cls.language:
            log.warn('Unable to determine preferred language (system: %r)', platform.system())
            return

        cls.language = 'sv'

        # Build list of languages
        languages = [cls.language]

        if '_' in cls.language:
            languages.append(cls.language.split('_', 1)[0])

        # Setup gettext
        try:
            cls.translation = gettext.translation(
                domain='trakt-for-plex',
                localedir=os.path.join(cls.path.locale),
                languages=languages
            )
        except Exception, ex:
            log.warn('Unable to initialize translation: %s', ex, exc_info=True)
            return

        log.info('Using languages: %r (translation: %r)', languages, cls.translation)

    @classmethod
    def get_pref(cls, key):
        try:
            return cls.prefs[key]
        except:
            return None

    @classmethod
    def _get_windows_locale(cls):
        try:
            import ctypes
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        except Exception, ex:
            log.warn('Unable to determine preferred language: %s', ex, exc_info=True)
            return None

        if lang_id not in locale.windows_locale:
            log.warn('Unknown language: %r', lang_id)
            return None

        return locale.windows_locale[lang_id]


def translate(message):
    if Environment.translation:
        return Environment.translation.ugettext(message)

    log.debug('Translations not initialized yet, falling back to original message: %r', message)
    return message
