import logging

log = logging.getLogger(__name__)


class MethodManager(object):
    def __init__(self, methods, single=True):
        self.methods = [
            (m.name, m) for m in methods
        ]
        self.single = single

    def filter(self, enabled):
        for name, method in self.methods:
            if enabled is not None and name not in enabled:
                log.debug('Method %r has been disabled', name)
                continue

            if not hasattr(method, 'test'):
                log.warn('Method %r is missing a test() method')
                continue

            if not method.test():
                log.info("Method %r is not available" % name)
                continue

            yield method

    def start(self, enabled=None):
        started = []

        for method in self.filter(enabled):
            obj = method()

            # Store reference
            started.append(obj)

            if self.single:
                break

        log.info(
            'Started %s method(s): %s',
            len(started),
            ', '.join([m.__class__.__name__ for m in started])
        )

        return started
