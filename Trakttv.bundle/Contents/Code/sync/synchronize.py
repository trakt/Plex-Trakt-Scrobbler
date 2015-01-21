from core.logger import Logger
from sync.sync_base import SyncBase


log = Logger('sync.synchronize')


class Synchronize(SyncBase):
    key = 'synchronize'
    title = "Synchronize"

    def run(self, **kwargs):
        self.reset()

        push = self.manager.handlers.get('push')
        pull = self.manager.handlers.get('pull')

        if not push or not pull:
            log.error("Sync handlers haven't initialized properly, unable to synchronize")
            self.update_status(False)
            return False

        self.check_stopping()

        if not pull.run():
            log.warn('Pull handler failed')
            status = pull.get_status()

            self.update_status(False, exceptions=status.exceptions)
            return False

        # Store missing media discovery artifacts
        self.store('missing.movies', pull.child('movie').retrieve('missing.movies'), single=True)
        self.store('missing.shows', pull.child('show').retrieve('missing.shows'), single=True)

        self.check_stopping()

        if not push.run(artifacts=self.artifacts):
            log.warn('Push handler failed')
            status = push.get_status()

            self.update_status(False, exceptions=status.exceptions)
            return False

        self.update_status(True)
        return True
