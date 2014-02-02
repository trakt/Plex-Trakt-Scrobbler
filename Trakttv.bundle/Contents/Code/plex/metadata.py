from core.cache import Cache
from core.eventing import EventManager
from core.logger import Logger
from plex.plex_base import PlexBase
from plex.plex_objects import PlexParsedGuid

log = Logger('plex.metadata')


class PlexMetadata(PlexBase):
    cache = Cache('metadata')

    @classmethod
    def initialize(cls):
        EventManager.subscribe('notifications.timeline.created', cls.timeline_created)
        EventManager.subscribe('notifications.timeline.deleted', cls.timeline_deleted)
        EventManager.subscribe('notifications.timeline.finished', cls.timeline_finished)

        cls.cache.on_refresh.subscribe(cls.on_refresh)

    @classmethod
    def on_refresh(cls, key):
        return cls.request('library/metadata/%s' % key)

    @classmethod
    def get(cls, key):
        return cls.cache.get(key, refresh=True)

    @classmethod
    def get_guid(cls, key):
        metadata = cls.get(key)
        if metadata is None:
            return None

        return metadata[0].get('guid')

    @classmethod
    def get_parsed_guid(cls, guid=None, key=None):
        if not guid:
            if not key:
                raise ValueError("Either guid or key is required")

            guid = cls.get_guid(key)

        return PlexParsedGuid.from_guid(guid)

    @classmethod
    def timeline_created(cls, item):
        log.debug('timeline_created(%s)', item)

    @classmethod
    def timeline_deleted(cls, item):
        log.debug('timeline_deleted(%s)', item)

        cls.cache.remove(str(item['itemID']))

    @classmethod
    def timeline_finished(cls, item):
        log.debug('timeline_finished(%s)', item)

        cls.cache.invalidate(str(item['itemID']), refresh=True, create=True)
