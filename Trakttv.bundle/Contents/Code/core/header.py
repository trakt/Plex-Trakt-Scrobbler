from core.plugin import PLUGIN_VERSION
import sys


class Header(object):
    @staticmethod
    def line(line):
        Log.Info('| ' + str(line))

    @staticmethod
    def separator(ch):
        Log.Info(ch * 50)

    @classmethod
    def show(cls):
        cls.separator('=')

        cls.line('Plex-Trakt-Scrobbler')
        cls.line('https://github.com/trakt/Plex-Trakt-Scrobbler')
        cls.separator('-')

        cls.line('Version: %s' % PLUGIN_VERSION)
        cls.separator('-')

        [cls.line(module_name) for module_name in cls.get_module_names()]
        cls.separator('=')

    @staticmethod
    def get_module_names():
        return sorted([
            module_name for (module_name, module) in sys.modules.items()
            if getattr(type(module), '__name__') == 'RestrictedModule'
        ])
