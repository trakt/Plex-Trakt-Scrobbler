from core.cache import Cache
from core.eventing import EventManager
from core.helpers import try_convert
from core.logger import Logger
from plex.plex_base import PlexBase
from plex.plex_matcher import PlexMatcher
from plex.plex_objects import PlexParsedGuid, PlexShow, PlexEpisode, PlexMovie
import re

log = Logger('plex.plex_metadata')

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
    'xbmcnfotv':        [
        ('imdb', r'(tt\d+)'),
        'thetvdb'
    ],
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
        for key, mappings in METADATA_AGENT_MAP.items():
            # Transform into list
            if type(mappings) is not list:
                mappings = [mappings]

            for x, value in enumerate(mappings):
                # Transform into tuple of length 2
                if type(value) is str:
                    value = (value, None)
                elif type(value) is tuple and len(value) == 1:
                    value = (value, None)

                # Compile pattern
                if value[1]:
                    value = (value[0], re.compile(value[1], re.IGNORECASE))

                mappings[x] = value

            METADATA_AGENT_MAP[key] = mappings

    @classmethod
    def on_refresh(cls, key):
        return cls.request('library/metadata/%s' % key)

    @classmethod
    def get_cache(cls, key):
        return cls.cache.get(key, refresh=True)

    @classmethod
    def get_guid(cls, key):
        metadata = cls.get_cache(key)
        if metadata is None:
            return None

        return metadata[0].get('guid')

    @classmethod
    def get(cls, key):
        data = cls.get_cache(key)
        if data is None:
            return None

        data = data[0]

        parsed_guid, item_key = cls.get_key(guid=data.get('guid'), required=False)

        # Create object for the data
        data_type = data.get('type')

        if data_type == 'movie':
            return PlexMovie.create(data, parsed_guid, item_key)

        if data_type == 'show':
            return PlexShow.create(data, parsed_guid, item_key)

        if data_type == 'episode':
            season, episodes = PlexMatcher.get_identifier(data)

            return PlexEpisode.create(data, season, episodes, parsed_guid=parsed_guid, key=item_key)

        log.warn('Failed to parse item "%s" with type "%s"', key, data_type)
        return None

    #
    # GUID/key parsing
    #

    @classmethod
    def get_parsed_guid(cls, key=None, guid=None, required=True):
        if not guid:
            if key:
                guid = cls.get_guid(key)
            elif required:
                raise ValueError("Either guid or key is required")
            else:
                return None

        return PlexParsedGuid.from_guid(guid)

    @classmethod
    def get_mapping(cls, parsed_guid):
        # Strip leading key
        agent = parsed_guid.agent[parsed_guid.agent.rfind('.') + 1:]

        # Return mapped agent and sid_pattern (if present)
        mappings = METADATA_AGENT_MAP.get(agent, [])

        if type(mappings) is not list:
            mappings = [mappings]

        for mapping in mappings:
            agent, sid_pattern = mapping

            if sid_pattern is None:
                return agent, None, None

            match = sid_pattern.match(parsed_guid.sid)
            if not match:
                continue

            return agent, sid_pattern, match

        return agent, None, None

    @classmethod
    def get_key(cls, key=None, guid=None, required=True):
        parsed_guid = cls.get_parsed_guid(key, guid, required)

        # Ensure service id is valid
        if not parsed_guid or not parsed_guid.sid:
            log.warn('Missing GUID or service identifier for item with ratingKey "%s" (parsed_guid: %s)', key, parsed_guid)
            return None, None

        agent, sid_pattern, match = cls.get_mapping(parsed_guid)

        parsed_guid.agent = agent

        # Match sid with regex
        if sid_pattern:
            if not match:
                log.warn('Failed to match "%s" against sid_pattern for "%s" agent', parsed_guid.sid, parsed_guid.agent)
                return None, None

            # Update with new sid
            parsed_guid.sid = ''.join(match.groups())

        return parsed_guid, (parsed_guid.agent, parsed_guid.sid)

    @staticmethod
    def add_identifier(data, p_item):
        service, sid = p_item['key'] if type(p_item) is dict else p_item.key

        # Parse identifier and append relevant '*_id' attribute to data
        if service == 'imdb':
            data['imdb_id'] = sid
            return data

        # Convert TMDB and TVDB identifiers to integers
        if service in ['themoviedb', 'thetvdb']:
            sid = try_convert(sid, int)

            # If identifier is invalid, ignore it
            if sid is None:
                return data

        if service == 'themoviedb':
            data['tmdb_id'] = sid

        if service == 'thetvdb':
            data['tvdb_id'] = sid

        return data

    #
    # Timeline Events
    #

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
