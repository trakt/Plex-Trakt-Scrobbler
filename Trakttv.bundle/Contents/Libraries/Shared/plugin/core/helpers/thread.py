from threading import Thread
import logging

log = logging.getLogger(__name__)


def spawn(func, *args, **kwargs):
    def wrapper(thread_name, args, kwargs):
        try:
            func(*args, **kwargs)
        except Exception, ex:
            log.error('Thread "%s" raised an exception: %s', thread_name, ex, exc_info=True)

    name = func.__name__

    thread = Thread(target=wrapper, name=name, args=args, kwargs=kwargs)
    thread.start()

    log.debug("Spawned thread with name '%s'" % name)
    return thread
