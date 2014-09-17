from plex import Plex
from plex_activity import Activity
from plex_metadata.core.defaults import DEFAULT_TYPES

import logging

log = logging.getLogger(__name__)


# TODO automatic invalidated object removal (+ manual trigger)
class Metadata(object):
    def __init__(self, types=None):
        if types is not None:
            self.types = types
        else:
            self.types = DEFAULT_TYPES

        self.cache = None

        # Bind activity events
        Activity.on('websocket.timeline.created', self.timeline_created)
        Activity.on('websocket.timeline.deleted', self.timeline_deleted)
        Activity.on('websocket.timeline.finished', self.timeline_finished)

    def configure(self, cache):
        self.cache = cache

    def get(self, key):
        # Try retrieve item from cache (if it exists)
        value = self.cache.get(key) if self.cache is not None else None

        if value is None:
            # Item not available in cache / no cache enabled
            value = self.fetch(key)

        if self.cache is not None:
            # Store in cache
            self.cache[key] = value

        return value

    #
    # Event handlers
    #

    def fetch(self, key):
        container = Plex['library'].metadata(key)

        items = list(container)

        if not items:
            log.warn('Unable to retrieve item, container empty')
            return None

        item = items[0]

        # Ignore if this is an unsupported media type
        if item.type not in self.types:
            # TODO set flag to ignore future refresh requests
            log.warn('Item %s with type "%s" has been ignored', key, item.type)
            return None

        return item

    #
    # Timeline event handlers
    #

    def timeline_created(self, item):
        pass

    def timeline_deleted(self, item):
        # TODO self.cache.remove(str(item['itemID']))
        pass

    def timeline_finished(self, item):
        # TODO self.cache.invalidate(str(item['itemID']), refresh=True, create=True)
        pass


# Global object
Default = Metadata()
