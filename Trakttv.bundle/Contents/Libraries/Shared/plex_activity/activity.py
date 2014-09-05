from plex_activity.sources import Logging, WebSocket

from pyemitter import Emitter
import logging

log = logging.getLogger(__name__)


class Activity(Emitter):
    registered = []

    def __init__(self, sources=None):
        self.available = self.get_available(sources)
        self.enabled = []

    def start(self):
        # TODO async start

        # Test methods until an available method is found
        for weight, source in self.available:
            if weight is None:
                # None = always start
                self.start_source(source)
            elif source.test():
                # Test passed
                self.start_source(source)
            else:
                log.info('activity source "%s" is not available', source.name)

        log.info(
            'Finished starting %s method(s): %s',
            len(self.enabled),
            ', '.join([('"%s"' % source.name) for source in self.enabled])
        )

    def start_source(self, source):
        instance = source(self)
        instance.start()

        self.enabled.append(instance)

    @classmethod
    def get_available(cls, sources):
        if sources:
            return [
                (weight, source) for (weight, source) in cls.registered
                if source.name in sources
            ]

        return cls.registered

    @classmethod
    def register(cls, source, weight=None):
        item = (weight, source)

        # weight = None, highest priority
        if weight is None:
            cls.registered.insert(0, item)
            return

        # insert in DESC order
        for x in xrange(len(cls.registered)):
            w, _ = cls.registered[x]

            if w is not None and w < weight:
                cls.registered.insert(x, item)
                return

        # otherwise append
        cls.registered.append(item)

# Register activity sources
Activity.register(WebSocket)
Activity.register(Logging, weight=1)
