import logging
import traceback

log = logging.getLogger(__name__)


class EventHandler(object):
    def __init__(self, key=None):
        self.key = key

        self.handlers = []

    def subscribe(self, handler):
        self.handlers.append(handler)
        return self

    def unsubscribe(self, handler):
        self.handlers.remove(handler)
        return self

    def fire(self, *args, **kwargs):
        single = kwargs.pop('single', False)

        results = []

        for handler in self.handlers:
            try:
                results.append(handler(*args, **kwargs))
            except Exception, e:
                log.warn(
                    'Exception in handler for event with key "%s", (%s) %s: %s',
                    self.key,
                    type(e),
                    e,
                    traceback.format_exc()
                )

        if single:
            return results[0] if results else None

        return results
