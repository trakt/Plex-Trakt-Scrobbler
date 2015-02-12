import logging

log = logging.getLogger(__name__)


class MethodManager(object):
    def __init__(self, methods):
        self.methods = [
            (__name__, m) for m in methods
        ]

    def filter(self):
        for name, method in self.methods:
            if not hasattr(method, 'test'):
                continue

            if not method.test():
                log.info("method %r is not available" % name)
                continue

            yield method

    def start(self):
        started = []

        for method in self.filter():
            obj = method()

            # Store reference
            started.append(obj)

        log.info(
            'Started %s method(s): %s',
            len(started),
            ', '.join([m.__class__.__name__ for m in started])
        )

        return started
