from core.eventing import EventManager
from core.logger import Logger
from plex.plex_base import PlexBase


SHOW_SID_REGEX = Regex('com.plexapp.agents.(thetvdb|abstvdb|xbmcnfotv)://([-a-z0-9\.]+)')

log = Logger('plex.metadata')


class PlexMetadata(PlexBase):
    @classmethod
    def initialize(cls):
        EventManager.subscribe('notifications.timeline.created', cls.timeline_created)
        EventManager.subscribe('notifications.timeline.deleted', cls.timeline_deleted)
        EventManager.subscribe('notifications.timeline.finished', cls.timeline_finished)

    @classmethod
    def get(cls, key):
        return cls.request('library/metadata/%s' % key)

    @classmethod
    def get_guid(cls, key):
        metadata = cls.get(key)
        if metadata is None:
            return None

        return metadata.xpath('//Directory')[0].get('guid')

    @classmethod
    def get_show_sid(cls, key):
        if not key:
            Log.Warn("SID matching failed, ratingKey isn't valid")
            return None

        guid = PlexMetadata.get_guid(key)

        match = SHOW_SID_REGEX.search(guid)
        if not match:
            Log.Warn('SID matching failed on guid: "%s"' % guid)
            return None

        return match.group(2)

    @classmethod
    def timeline_created(cls, item):
        log.debug('timeline_created(%s)', item)

    @classmethod
    def timeline_deleted(cls, item):
        log.debug('timeline_deleted(%s)', item)

    @classmethod
    def timeline_finished(cls, item):
        log.debug('timeline_finished(%s)', item)
