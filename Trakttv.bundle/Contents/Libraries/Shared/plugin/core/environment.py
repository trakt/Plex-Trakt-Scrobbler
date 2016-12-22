from plugin.core.constants import PLUGIN_IDENTIFIER

import gettext
import locale
import logging
import os
import platform

DEFAULT_LOCALE = 'en_US'

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
    def home(self):
        return os.path.abspath(os.path.join(self.plugin_support, '..'))

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
        # Use language defined in preferences (if available)
        language = cls.get_pref('language') or ''

        # Initialize locale
        try:
            locale.setlocale(locale.LC_ALL, language)
        except ValueError as ex:
            # Ignore locale emulation exceptions
            if ex.message == '_locale emulation only supports "C" locale':
                log.info('Locale extension not available, using the "C" locale')
                return False

            # Unknown exception
            log.warn('Unable to set locale to %r: %s', language, ex, exc_info=True)
            return False
        except Exception as ex:
            log.warn('Unable to set locale to %r: %s', language, ex, exc_info=True)
            return False

        # Default to the "en_US" locale
        code, _ = locale.getlocale()

        if not code:
            try:
                locale.setlocale(locale.LC_ALL, DEFAULT_LOCALE)
            except ValueError as ex:
                # Ignore locale emulation exceptions
                if ex.message == '_locale emulation only supports "C" locale':
                    log.info('Locale extension not available, using the "C" locale')
                    return False

                # Unknown exception
                log.warn('Unable to set locale to %r: %s', language, ex, exc_info=True)
                return False
            except Exception as ex:
                log.warn('Unable to set locale to %r: %s', DEFAULT_LOCALE, ex, exc_info=True)
                return False

        log.info('Using locale: %r', locale.getlocale())
        return True

    @classmethod
    def setup_translation(cls):
        # Retrieve preferred language
        try:
            cls.language = cls._get_language()
        except Exception as ex:
            log.warn('Unable to retrieve preferred language: %s', ex, exc_info=True)
            cls.language = None
            return

        if not cls.language:
            log.warn('Unable to determine preferred language (system: %r)', platform.system())
            return

        # Build list of languages
        languages = [cls.language]

        if '_' in cls.language:
            languages.append(cls.language.split('_', 1)[0])

        # Check if language exists
        found = False

        for lang in languages:
            if os.path.exists(os.path.join(cls.path.locale, lang)):
                found = True
                break

        if not found:
            log.info('No translation available for %r', languages)
            return

        # Setup gettext
        try:
            cls.translation = gettext.translation(
                domain='channel',
                localedir=os.path.join(cls.path.locale),
                languages=languages
            )
        except Exception as ex:
            log.warn('Unable to initialize languages: %r - %s', languages, ex, exc_info=True)
            return

        log.info('Using languages: %r (translation: %r)', languages, cls.translation)

    @classmethod
    def get_pref(cls, key):
        try:
            return cls.prefs[key]
        except:
            return None

    @classmethod
    def _get_language(cls):
        # Use language defined in preferences (if available)
        language = cls.get_pref('language')

        if language:
            return language.lower()

        # Use system language
        if platform.system() == 'Windows':
            # Retrieve windows user language
            return cls._get_windows_default_language()

        # Retrieve current locale
        code, _ = locale.getdefaultlocale()

        # Ensure language code is valid
        if not code or type(code) is not str:
            log.info('Unable to detect system language, defaulting to the "%s" locale', DEFAULT_LOCALE)
            return DEFAULT_LOCALE.lower()

        # Parse language code
        if len(code) == 2:
            return code.lower()
        elif len(code) > 2 and code[2] == '_':
            return code[:5].lower()

        log.warn('Unknown language code: %r', code)
        return None

    @classmethod
    def _get_windows_default_language(cls):
        try:
            import ctypes
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        except Exception as ex:
            log.warn('Unable to determine preferred language: %s', ex, exc_info=True)
            return None

        if lang_id not in locale.windows_locale:
            log.warn('Unknown language: %r', lang_id)
            return None

        return locale.windows_locale[lang_id].lower()


def translate(message):
    if Environment.translation:
        return Environment.translation.ugettext(message)

    return message
