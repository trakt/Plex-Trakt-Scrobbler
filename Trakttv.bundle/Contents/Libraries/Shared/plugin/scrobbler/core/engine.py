from plugin.scrobbler.core.constants import IGNORED_EVENTS

import logging

log = logging.getLogger(__name__)


class Engine(object):
    handlers = {}

    def __init__(self):
        self.handlers = self._construct_handlers(self.handlers)

    def process(self, obj, events):
        for key, payload in events:
            result = self.process_one(obj, key, payload)

            if not result:
                continue

            for item in result:
                yield item

    def process_one(self, obj, key, payload):
        # Ensure the event hasn't been ignored
        if key in IGNORED_EVENTS:
            log.debug('Ignored %r event', key)
            return

        # Try find handler for event
        handlers = self.handlers.get(key)

        if not handlers:
            raise Exception('No handlers found for %r event' % key)

        # Run handlers until we get a result
        result = None

        for h in handlers:
            if not h.is_valid_source(obj.state):
                log.info('Ignoring %r event for %r, invalid state transition', key, obj)
                continue

            result = h.process(obj, payload)
            break

        if result is None:
            return

        for item in result:
            if not item:
                continue

            state, data = item

            # Update current state/data
            self._set_attributes(obj, **data)

            if state is None:
                continue

            # New event
            obj.state = state

            # Save
            obj.save()

            yield state, data

    @staticmethod
    def find_handlers(handlers, func):
        result = []

        for h in handlers:
            if not func(h):
                continue

            result.append(h)

        return result

    @classmethod
    def register(cls, kls):
        key = kls.__event__

        if not key:
            raise Exception('Unable to register %r, missing "__key__" attribute' % kls)

        if key not in cls.handlers:
            cls.handlers[key] = []

        cls.handlers[key].append(kls)

    @staticmethod
    def _construct_handlers(handlers):
        result = {}

        for key, classes in handlers.items():
            objects = []

            for kls in classes:
                objects.append(kls())

            result[key] = objects

        return result

    @staticmethod
    def _set_attributes(obj, **kwargs):
        for key, value in kwargs.items():
            if not hasattr(obj, key):
                raise Exception('Object %r is missing the attribute %r' % (obj, key))

            setattr(obj, key, value)


class SessionEngine(Engine):
    handlers = {}
