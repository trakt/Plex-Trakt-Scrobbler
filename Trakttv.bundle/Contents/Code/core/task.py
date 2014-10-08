from core.helpers import spawn
from core.logger import Logger

from threading import Lock
import sys
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
            self.lock.acquire()

        if self.exception:
            raise self.exception[1], None, self.exception[2]

        return self.result

    def run(self):
        if self.started:
            return

        self.lock.acquire()
        self.started = True

        try:
            self.result = self.target(*self.args, **self.kwargs)
        except CancelException, e:
            self.exception = sys.exc_info()

            log.debug('Task cancelled')
        except Exception, e:
            self.exception = sys.exc_info()

            log.warn('Exception raised in triggered function %s (%s) %s: %s' % (
                self.target, type(e), e, traceback.format_tb(self.exception[2])
            ))

        self.complete = True
        self.lock.release()
