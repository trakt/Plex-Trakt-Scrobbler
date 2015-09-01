import functools
import logging
import warnings

try:
    import arrow
except ImportError:
    arrow = None

log = logging.getLogger(__name__)


def from_iso8601(value):
    if value is None:
        return None

    if arrow is None:
        raise Exception('"arrow" module is not available')

    # Parse ISO8601 datetime
    dt = arrow.get(value)

    # Convert to UTC
    dt = dt.to('UTC')

    # Return datetime object
    return dt.datetime


def to_iso8601(value):
    if value is None:
        return None

    return value.strftime('%Y-%m-%dT%H:%M:%S') + '.000-00:00'


def deprecated(message):
    def wrap(func):
        @functools.wraps(func)
        def wrapped(self, *args, **kwargs):
            warnings.warn(message, DeprecationWarning, stacklevel=2)

            return func(self, *args, **kwargs)

        return wrapped

    return wrap


def synchronized(f_lock, mode='full'):
    if mode == 'full':
        mode = ['acquire', 'release']
    elif isinstance(mode, (str, unicode)):
        mode = [mode]

    def wrap(func):
        @functools.wraps(func)
        def wrapped(self, *args, **kwargs):
            lock = f_lock(self)

            def acquire():
                if 'acquire' not in mode:
                    return

                lock.acquire()

            def release():
                if 'release' not in mode:
                    return

                lock.release()

            # Acquire the lock
            acquire()

            try:
                # Execute wrapped function
                result = func(self, *args, **kwargs)
            finally:
                # Release the lock
                release()

            # Return the result
            return result

        return wrapped

    return wrap
