from plugin.core.constants import PLUGIN_IDENTIFIER

import os


class PathEnvironment(object):
    # TODO confirm validity of this on *nix and OS X

    def __init__(self, core):
        self._core = core

        self._plugin_support = None

    @property
    def code(self):
        return self._core.code_path

    @property
    def libraries(self):
        return os.path.abspath(os.path.join(self.code, '..', 'Libraries'))

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


class Environment(object):
    dict = None
    path = None
    prefs = None

    @classmethod
    def setup(cls, core, dict, platform, prefs):
        cls.path = PathEnvironment(core)
        cls.dict = dict
        cls.platform = PlatformEnvironment(platform)
        cls.prefs = prefs

    @classmethod
    def get_pref(cls, key):
        try:
            return cls.prefs[key]
        except:
            return None
