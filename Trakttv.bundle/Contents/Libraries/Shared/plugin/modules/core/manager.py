import logging

log = logging.getLogger(__name__)


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
    def discover(cls):
        from plugin.modules.scheduler.main import Scheduler
        from plugin.modules.sessions.main import Sessions
        from plugin.modules.upgrade.main import Upgrade

        return [
            Scheduler,
            Sessions,
            Upgrade
        ]

    @classmethod
    def construct(cls):
        try:
            available = cls.discover()
        except Exception, ex:
            log.error('Unable to import modules: %s', ex, exc_info=True)
            return

        constructed = []

        for module in available:
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
                log.warn('Unable to start %r module - %s', key, ex, exc_info=True)

        log.debug('Started %d module(s): %s', len(started), ', '.join(started))

    def get(self, key, default=None):
        return self.modules.get(key, default)
