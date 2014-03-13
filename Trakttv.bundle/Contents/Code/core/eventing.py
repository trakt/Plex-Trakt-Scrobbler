from core.helpers import join_attributes
from core.logger import Logger
import traceback

# Keys of events that shouldn't be logged
SILENT_FIRE = [
    'sync.get_cache_id'
]

log = Logger('core.eventing')


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


class EventManager(object):
    events = {}

    @classmethod
    def ensure_exists(cls, key):
        if key in cls.events:
            return

        cls.events[key] = EventHandler(key)

    @classmethod
    def subscribe(cls, key, handler):
        cls.ensure_exists(key)
        cls.events[key].subscribe(handler)

    @classmethod
    def unsubscribe(cls, key, handler):
        if key not in cls.events:
            return False

        cls.events[key].unsubscribe(handler)

        # Remove event if it doesn't have any handlers now
        if len(cls.events[key].handlers) < 1:
            cls.events.pop(key)

        return True

    @classmethod
    def fire(cls, key, *args, **kwargs):
        if key not in SILENT_FIRE:
            attributes = join_attributes(args=args, kwargs=kwargs)

        cls.ensure_exists(key)
        return cls.events[key].fire(*args, **kwargs)
