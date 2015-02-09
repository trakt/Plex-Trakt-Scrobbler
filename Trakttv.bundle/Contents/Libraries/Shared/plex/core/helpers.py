def to_iterable(value):
    if value is None:
        return None

    if isinstance(value, (list, tuple)):
        return value

    return [value]


def synchronized(func):
    def wrapper(self, *__args, **__kw):
        self._lock.acquire()

        try:
            return func(self, *__args, **__kw)
        finally:
            self._lock.release()

    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__

    return wrapper
