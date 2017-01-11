from plex.lib import six

import functools
import inspect
import re
import unicodedata


def flatten(text):
    if text is None:
        return None

    # Normalize `text` to ascii
    text = normalize(text)

    # Remove special characters
    text = re.sub('[^A-Za-z0-9\s]+', '', text)

    # Merge duplicate spaces
    text = ' '.join(text.split())

    # Convert to lower-case
    return text.lower()


def normalize(text):
    if text is None:
        return None

    # Normalize unicode characters
    if type(text) is six.text_type:
        text = unicodedata.normalize('NFKD', text)

    # Ensure text is ASCII, ignore unknown characters
    text = text.encode('ascii', 'ignore')

    # Return decoded `text`
    return text.decode('ascii')


def to_iterable(value):
    if value is None:
        return None

    if isinstance(value, (list, tuple)):
        return value

    return [value]


def synchronized(f_lock, mode='full'):
    if inspect.isfunction(f_lock) and f_lock.__name__ != '<lambda>':
        return synchronized(lambda self: self._lock, mode)(f_lock)

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
