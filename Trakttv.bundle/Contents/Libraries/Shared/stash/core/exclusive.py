from stash.lib import six

from threading import Condition, Lock


class ExclusiveContext(object):
    def __init__(self):
        self.active = False

        self.lock = Lock()
        self.condition = Condition(self.lock)

    def __enter__(self):
        self.condition.acquire()
        self.active = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.active = False
        self.condition.notify_all()

        self.condition.release()


def operation(prop='exclusive'):
    def outer(func):
        def inner(self, *args, **kwargs):
            force = kwargs.pop('__force', False)

            # Bypass exclusive lock if "__force" is enabled
            if force:
                return func(self, *args, **kwargs)

            # Retrieve `Exclusive` object for `self`
            if isinstance(prop, six.string_types):
                exclusive = getattr(self, prop)
            else:
                raise ValueError('Unknown value provided for "prop": %r', prop)

            if exclusive is None:
                raise ValueError('Unable to find %r property on %r', prop, self)

            # Acquire condition lock
            exclusive.condition.acquire()

            if exclusive.active:
                # Wait for exclusive access to be released
                exclusive.condition.wait()

            try:
                # Run operation
                return func(self, *args, **kwargs)
            finally:
                # Release condition lock
                exclusive.condition.release()

        return inner

    return outer
