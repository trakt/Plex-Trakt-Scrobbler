from plex import Plex
from plex.core.helpers import synchronized
from plex_activity import Activity
from plex_metadata.core.defaults import DEFAULT_TYPES

from threading import Condition
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
        self.client = None

        # Private
        self._lock = Condition()

        # Bind activity events
        Activity.on('websocket.timeline.created', self.timeline_created)
        Activity.on('websocket.timeline.deleted', self.timeline_deleted)
        Activity.on('websocket.timeline.finished', self.timeline_finished)

    def configure(self, cache=None, client=None):
        self.cache = self.cache or cache
        self.client = self.client or client

    @synchronized
    def get(self, key):
        try:
            # Try retrieve item from cache (if it exists)
            value = self._cache_get(key)
        except Exception, ex:
            log.warn('Unable to retrieve item "%s" from cache - %s', key, ex, exc_info=True)
            value = None

        if value is None:
            # Item not available in cache / no cache enabled
            value = self.refresh(key)

        return value

    @synchronized
    def invalidate(self, key):
        try:
            # Invalidate item in cache
            self._cache_invalidate(key)
        except Exception, ex:
            log.warn('Unable to invalidate item "%s" from cache - %s', key, ex, exc_info=True)

    @synchronized
    def refresh(self, key):
        # Item not available in cache / no cache enabled
        value = self.fetch(key)

        try:
            # Store in cache
            self._cache_store(key, value)
        except Exception, ex:
            log.warn('Unable to store item "%s" in cache - %s', key, ex, exc_info=True)

        return value

    #
    # Cache methods
    #

    def _cache_get(self, key):
        if self.cache is None:
            return None

        value = self.cache.get(key)

        if value is None:
            return None

        # Validate item
        if not value.guid:
            self._cache_invalidate(key)
            return None

        # Update `client` attribute
        value.client = self.client

        return value

    def _cache_invalidate(self, key):
        if self.cache is None:
            return

        del self.cache[key]

    def _cache_store(self, key, value):
        if self.cache is None:
            return

        if not value or not value.guid:
            return

        self.cache[key] = value

    #
    # Event handlers
    #

    def fetch(self, key):
        # Request metadata from server
        container = Plex['library'].metadata(key)

        if not container:
            log.warn('Metadata request for item "%s" failed', key)
            return None

        # Cast to `list` (resolve iterators)
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
