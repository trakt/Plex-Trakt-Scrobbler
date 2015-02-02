from plugin.modules.backup.main import Backup

import logging

log = logging.getLogger(__name__)

MODULES = [
    Backup
]


class ModuleManagerMeta(type):
    def __getitem__(self, key):
        return self.modules[key]


class ModuleManager(object):
    __metaclass__ = ModuleManagerMeta

    modules = {}

    @classmethod
    def initialize(cls):
        cls.modules = dict(cls.construct())

    @classmethod
    def construct(cls):
        constructed = []

        for module in MODULES:
            try:
                if module.__key__ is None:
                    # Automatically set module `__key__` (if one isn't specified)
                    module.__key__ = module.__class__.__name__.lower()

                yield module.__key__, module()

                constructed.append(module.__key__)
            except Exception, ex:
                log.warn('Unable to construct module: %r', module)

        log.debug('Constructed %d module(s): %s', len(constructed), ', '.join(constructed))

    @classmethod
    def start(cls):
        started = []

        for key, module in cls.modules.items():
            try:
                module.start()

                started.append(key)
            except Exception, ex:
                log.warn('Unable to start module: %r', module)

        log.debug('Started %d module(s): %s', len(started), ', '.join(started))

    def get(self, key, default=None):
        return self.modules.get(key, default)
