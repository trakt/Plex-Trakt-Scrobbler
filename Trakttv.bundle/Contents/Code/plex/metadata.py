from core.cache import Cache
from core.eventing import EventManager
from core.logger import Logger
from plex.plex_base import PlexBase
from plex.plex_objects import PlexParsedGuid
import re

log = Logger('plex.metadata')

# Mappings for agents to their compatible service
METADATA_AGENT_MAP = {
    # Multi
    'mcm':              ('thetvdb', r'MCM_TV_A_(.*)'),

    # Movie
    'xbmcnfo':          'imdb',
    'standalone':       'themoviedb',

    # TV
    'abstvdb':          'thetvdb',
    'thetvdbdvdorder':  'thetvdb',
    'xbmcnfotv':        'thetvdb',
}


class PlexMetadata(PlexBase):
    cache = Cache('metadata')

    @classmethod
    def initialize(cls):
        EventManager.subscribe('notifications.timeline.created', cls.timeline_created)
        EventManager.subscribe('notifications.timeline.deleted', cls.timeline_deleted)
        EventManager.subscribe('notifications.timeline.finished', cls.timeline_finished)

        cls.cache.on_refresh.subscribe(cls.on_refresh)

        # Compile agent mapping patterns
        for key, value in METADATA_AGENT_MAP.items():
            # Transform into tuple of length 2
            if type(value) is str:
                value = (value, None)
            elif type(value) is tuple and len(value) == 1:
                value = (value, None)

            # Compile pattern
            if value[1]:
                value = (value[0], re.compile(value[1], re.IGNORECASE))

            # Update dictionary
            METADATA_AGENT_MAP[key] = value

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
    def get_mapping(cls, agent):
        # Strip leading key
        agent = agent[agent.rfind('.') + 1:]

        # Return if there is no mapping present
        if agent not in METADATA_AGENT_MAP:
            return agent, None

        # Return mapped agent and sid_pattern (if present)
        return METADATA_AGENT_MAP.get(agent)

    @classmethod
    def get_key(cls, key):
        parsed_guid = cls.get_parsed_guid(key=key)

        # Ensure service id is valid
        if not parsed_guid or not parsed_guid.sid:
            log.warn('Missing GUID or service identifier for item with ratingKey "%s" (parsed_guid: %s)', key, parsed_guid)
            return None, None

        agent, sid_pattern = cls.get_mapping(parsed_guid.agent)

        # Match sid with regex
        if sid_pattern:
            match = sid_pattern.match(parsed_guid.sid)

            if not match:
                log.warn('Failed to match "%s" against sid_pattern for "%s" agent', parsed_guid.sid, parsed_guid.agent)
                return None, None

            # Update with new sid
            parsed_guid.sid = ''.join(match.groups())

        return parsed_guid, (agent, parsed_guid.sid)

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
