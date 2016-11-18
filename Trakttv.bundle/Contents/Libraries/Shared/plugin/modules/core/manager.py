from plugin.core.message import InterfaceMessages

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
        from plugin.modules.mapper.main import Mapper
        from plugin.modules.matcher.main import Matcher
        from plugin.modules.scheduler.main import Scheduler
        from plugin.modules.sessions.main import Sessions
        from plugin.modules.upgrade.main import Upgrade

        return [
            Mapper,
            Matcher,
            Scheduler,
            Sessions,
            Upgrade
        ]

    @classmethod
    def construct(cls):
        if InterfaceMessages.critical:
            log.info('Module construction has been cancelled due to a critical plugin error')
            return

        try:
            available = cls.discover()
        except Exception as ex:
            log.error('Unable to import modules: %s', ex, exc_info=True)
            return

        # Construct modules
        constructed = []

        for module in available:
            if InterfaceMessages.critical:
                log.info('Module construction has been cancelled due to a critical plugin error')
                return

            try:
                if module.__key__ is None:
                    # Automatically set module `__key__` (if one isn't specified)
                    module.__key__ = module.__class__.__name__.lower()

                yield module.__key__, module()

                constructed.append(module.__key__)
            except Exception as ex:
                log.warn('Unable to construct module: %r', module)

        log.debug('Constructed %d module(s): %s', len(constructed), ', '.join(constructed))

    @classmethod
    def start(cls, keys=None):
        if InterfaceMessages.critical:
            log.info('Module startup has been cancelled due to a critical plugin error')
            return

        # Start modules
        started = []

        for key, module in cls.modules.items():
            if keys is not None and key not in keys:
                continue

            if InterfaceMessages.critical:
                log.info('Module startup has been cancelled due to a critical plugin error')
                return

            try:
                module.start()

                started.append(key)
            except Exception as ex:
                log.warn('Unable to start %r module - %s', key, ex, exc_info=True)

        log.debug('Started %d module(s): %s', len(started), ', '.join(started))

    def get(self, key, default=None):
        return self.modules.get(key, default)
