from core.helpers import spawn
from core.logger import Logger

from threading import Lock
import sys
import trakt
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

        # Wait for the task to finish
        if not self.complete:
            # Wait for lock
            self.lock.acquire()

            # Release it again
            self.lock.release()

        if self.exception or not self.complete:
            return None

        return self.result

    def target_name(self):
        if self.target is None:
            return None

        func_name = getattr(self.target, '__name__', None)

        kls = getattr(self.target, 'im_class', None)
        kls_name = getattr(kls, '__name__', None) if kls else None

        if kls_name and func_name:
            return '%s.%s()' % (kls_name, func_name)

        if func_name:
            return '%s()' % func_name

        return None

    def run(self):
        # Wait for lock
        self.lock.acquire()

        # Ensure task hasn't already been started
        if self.started:
            self.lock.release()
            return

        self.started = True

        try:
            # Call task
            self.result = self.target(*self.args, **self.kwargs)
        except CancelException, e:
            self.exception = sys.exc_info()

            log.debug('Task cancelled')
        except trakt.RequestError, e:
            self.exception = sys.exc_info()

            log.warn('trakt.tv request failed: %s', e)
        except Exception, ex:
            self.exception = sys.exc_info()

            log.error('Exception raised in triggered function %r: %s', self.target_name(), ex, exc_info=True)
        finally:
            # Release lock
            self.complete = True
            self.lock.release()

