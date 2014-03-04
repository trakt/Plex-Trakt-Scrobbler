from core.helpers import spawn
from core.logger import Logger
from threading import Lock
import traceback

log = Logger('core.task')


class CancelException(Exception):
    pass


class Task(object):
    def __init__(self, target, *args, **kwargs):
        self.target = target
        self.args = args
        self.kwargs = kwargs

        self.exception = None
        self.result = None

        self.complete = False
        self.started = False
        self.lock = Lock()

    def spawn(self, name):
        spawn(self.run, thread_name=name)

    def wait(self):
        if not self.started:
            return False

        if not self.complete:
            log.debug('(%s) Trying to acquire lock', self.target)

            self.lock.acquire()

            log.debug('(%s) Acquired lock', self.target)

        if self.exception:
            raise self.exception

        return self.result

    def run(self):
        if self.started:
            return

        self.lock.acquire()
        self.started = True
        log.debug('Started task for target %s', self.target)

        try:
            self.result = self.target(*self.args, **self.kwargs)
        except CancelException, e:
            self.exception = e

            log.info('Task cancelled')
        except Exception, e:
            self.exception = e

            log.warn('Exception raised in triggered function %s (%s) %s: %s' % (
                self.target, type(e), e, traceback.format_exc()
            ))

        log.debug('Finished task for target %s', self.target)
        self.complete = True
        self.lock.release()
