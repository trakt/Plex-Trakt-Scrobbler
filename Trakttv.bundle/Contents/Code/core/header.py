from plugin.core.constants import PLUGIN_VERSION, PLUGIN_NAME

import sys


class Header(object):
    @staticmethod
    def line(line):
        Log.Info('| ' + str(line))

    @staticmethod
    def separator(ch):
        Log.Info(ch * 50)

    @classmethod
    def show(cls, main):
        cls.separator('=')

        cls.line(PLUGIN_NAME)
        cls.line('https://github.com/trakt/Plex-Trakt-Scrobbler')
        cls.separator('-')

        cls.print_version(main)
        cls.separator('-')

        if Dict['developer']:
            cls.line('Developer Mode: Enabled')
            cls.separator('-')

        [cls.line(module_name) for module_name in cls.get_module_names()]
        cls.separator('=')

    @classmethod
    def print_version(cls, main):
        cls.line('Current Version: v%s' % PLUGIN_VERSION)

    @staticmethod
    def get_module_names():
        return sorted([
            module_name for (module_name, module) in sys.modules.items()
            if getattr(type(module), '__name__') == 'RestrictedModule'
        ])
