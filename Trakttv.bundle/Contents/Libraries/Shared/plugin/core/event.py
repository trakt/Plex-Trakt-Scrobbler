from threading import Lock
import logging
import traceback

log = logging.getLogger(__name__)


class Event(list):
    def fire(self, *args, **kwargs):
        return self(*args, **kwargs)

    def subscribe(self, func):
        self.append(func)

    def set(self, func):
        # Remove any existing functions
        for x in self:
            self.remove(x)

        # Store new function
        self.append(func)

    def __call__(self, *args, **kwargs):
        single = kwargs.pop('single', False)

        results = []

        for f in self:
            result = None

            try:
                result = f(*args, **kwargs)
            except Exception, ex:
                log.warn('Exception raised in event: %s - %s', ex, traceback.format_exc())
                continue

            if result and single:
                return result
            else:
                results.append(result)

        if single:
            return None

        return results


class EventCollection(object):
    def __init__(self):
        self.events = {}
        self.lock = Lock()

    def __getitem__(self, key):
        with self.lock:
            if key not in self.events:
                self.events[key] = Event()

            return self.events[key]


Global = EventCollection()
