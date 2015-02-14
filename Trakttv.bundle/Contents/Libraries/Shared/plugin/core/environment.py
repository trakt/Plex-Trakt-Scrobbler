from plugin.core.constants import PLUGIN_IDENTIFIER

import os


class PathEnvironment(object):
    # TODO confirm validity of this on *nix and OS X

    def __init__(self, core):
        self._core = core

    @property
    def code(self):
        return self._core.code_path

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
        base_path = self.code[:self.code.index(os.path.sep + 'Plug-ins')]

        return os.path.join(base_path, 'Plug-in Support')


class Environment(object):
    dict = None
    path = None
    prefs = None

    @classmethod
    def setup(cls, core, dict, prefs):
        cls.path = PathEnvironment(core)
        cls.dict = dict
        cls.prefs = prefs
