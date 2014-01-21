from core.logger import Logger
from sync.sync_base import SyncBase


log = Logger('sync.synchronize')


class Synchronize(SyncBase):
    key = 'synchronize'
    title = "Synchronize"

    def run(self, **kwargs):
        log.debug('Synchronize.run kwargs: %s' % kwargs)

        push = self.manager.handlers.get('push')
        pull = self.manager.handlers.get('pull')

        if not push or not pull:
            log.warn("Sync handlers haven't initialized properly, unable to synchronize")
            return False

        if not pull.run():
            log.warn("Pull handler failed")
            return False

        if not push.run():
            log.warn('Push handler failed')
            return False

        return True
