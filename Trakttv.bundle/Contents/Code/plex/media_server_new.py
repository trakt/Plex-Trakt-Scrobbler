from core.helpers import all, try_convert
from core.logger import Logger
from plex.metadata import PlexMetadata
from plex.plex_base import PlexBase
from plex.plex_objects import PlexShow, PlexEpisode, PlexMovie
from caper import Caper
import types
import os

log = Logger('plex.media_server_new')


# Mappings for agents to their compatible service
METADATA_AGENT_MAP = {
    'xbmcnfo': 'imdb',
    'xbmcnfotv': 'thetvdb'
}


IDENTIFIER_MISMATCH = 'Identifier parsing mismatch on "%s" (%s), using plex identifier'


class PlexMediaServer(PlexBase):
    parser = None

    @classmethod
    def get_parser(cls):
        """
        :rtype: Caper
        """
        if cls.parser is None:
            log.info('Initializing caper parsing library')
            cls.parser = Caper()

        return cls.parser

    @classmethod
    def get_server_info(cls, quiet=False):
        return cls.request(quiet=quiet)

    @classmethod
    def get_sections(cls, types=None, keys=None, cache_id=None):
        """Get the current sections available on the server, optionally filtering by type and/or key

        :param types: Section type filter
        :type types: str or list of str

        :param keys: Section key filter
        :type keys: str or list of str

        :return: List of sections found
        :rtype: (type, key, title)
        """

        if types and isinstance(types, basestring):
            types = [types]

        if keys and isinstance(keys, basestring):
            keys = [keys]

        container = cls.request('library/sections', cache_id=cache_id)

        sections = []
        for section in container:
            # Try retrieve section details - (type, key, title)
            section = (
                section.get('type', None),
                section.get('key', None),
                section.get('title', None)
            )

            # Validate section, skip over bad sections
            if not all(x for x in section):
                continue

            # Apply key filter
            if keys is not None and section[1] not in keys:
                continue

            # Apply type filter
            if types is not None and section[0] not in types:
                continue

            sections.append(section)

        return sections

    @classmethod
    def get_section(cls, key, cache_id=None):
        return cls.request('library/sections/%s/all' % key, timeout=10, cache_id=cache_id)

    @classmethod
    def get_directories(cls, key, cache_id=None):
        section = cls.get_section(key, cache_id=cache_id)
        if section is None:
            return []

        return section.xpath('//Directory')

    @classmethod
    def get_videos(cls, key, cache_id=None):
        section = cls.get_section(key, cache_id=cache_id)
        if section is None:
            return []

        return section.xpath('//Video')

    @classmethod
    def get_agent_mapping(cls, agent):
        # Strip leading key
        agent = agent[agent.rfind('.') + 1:]

        # Return if there is no mapping present
        if agent not in METADATA_AGENT_MAP:
            return agent, None

        # Return mapped agent and sid_pattern (if present)
        mapping = METADATA_AGENT_MAP.get(agent)

        if type(mapping) is not tuple:
            mapping = (mapping, None)

        if len(mapping) == 1:
            return mapping[0], None

        return mapping


    @classmethod
    def get_library_key(cls, key):
        parsed_guid = PlexMetadata.get_parsed_guid(key=key)

        # Ensure service id is valid
        if not parsed_guid or not parsed_guid.sid:
            log.warn('Missing GUID or service identifier for item with ratingKey "%s" (parsed_guid: %s)', key, parsed_guid)
            return None, None

        agent, sid_pattern = cls.get_agent_mapping(parsed_guid.agent)

        if sid_pattern:
            raise NotImplementedError()

        return parsed_guid, (agent, parsed_guid.sid)

    @classmethod
    def map_library_item(cls, table, data):
        # Get the key for the item
        parsed_guid, key = cls.get_library_key(data.get('ratingKey'))
        if parsed_guid is None:
            return False

        if key not in table:
            table[key] = []

        # Create object for the data
        data_type = data.get('type')
        if data_type == 'movie':
            item = PlexMovie.create(data, parsed_guid, key)
        elif data_type == 'show':
            item = PlexShow.create(data, parsed_guid, key)
        else:
            log.info('Unknown item "%s" with type "%s"', data.get('ratingKey'), data_type)
            return False

        # Map item into table
        table[key].append(item)
        return True

    @classmethod
    def get_library(cls, types=None, keys=None, cache_id=None):
        if types and isinstance(types, basestring):
            types = [types]

        # Get all sections or filter based on 'types' and 'sections'
        sections = [(type, key) for (type, key, _) in cls.get_sections(types, keys, cache_id=cache_id)]

        movies = {}
        shows = {}

        for type, key in sections:
            if type == 'movie':
                for video in cls.get_videos(key, cache_id=cache_id):
                    cls.map_library_item(movies, video)

            if type == 'show':
                for directory in cls.get_directories(key, cache_id=cache_id):
                    cls.map_library_item(shows, directory)

        if len(types) == 1:
            if types[0] == 'movie':
                return movies

            if types[0] == 'show':
                return shows

        return movies, shows

    @staticmethod
    def merge_dicts(dicts):
        result = {}

        for d in dicts:
            for key, value in d.items():
                if key in result:
                    # Multiple items, append or switch to list
                    if isinstance(result[key], list):
                        result[key].append(value)
                    else:
                        result[key] = [result[key], value]
                else:
                    result[key] = value

        return result

    @classmethod
    def merge_info(cls, info):
        result = {}

        for key, value in info.items():
            if not isinstance(value, list):
                continue

            if isinstance(value[0], dict):
                result[key] = cls.merge_dicts(value)
            else:
                result[key] = value

        return result

    @classmethod
    def get_chain_identifier(cls, info):
        info = cls.merge_info(info)
        identifier = info.get('identifier')

        for key, value in identifier.items():
            if key not in ['season', 'episode', 'episode_from', 'episode_to']:
                continue

            if isinstance(value, types.StringTypes):
                identifier[key] = try_convert(value, int)
            elif isinstance(value, list):
                # For repeat style identifiers (S01E10E11, etc..)
                identifier[key] = [try_convert(x, int) for x in value]

        return identifier

    @classmethod
    def get_episode_identifier(cls, video):
        # Parse filename for extra info
        parts = video.find('Media').findall('Part')
        if not parts:
            log.warn('Item "%s" has no parts', video.get('ratingKey'))
            return None, []

        # Get just the name of the first part (without full path and extension)
        file_name = os.path.splitext(os.path.basename(parts[0].get('file')))[0]

        # TODO what is the performance of this like?
        # TODO maybe add the ability to disable this in settings ("Identification" option, "Basic" or "Accurate")
        extended = cls.get_parser().parse(file_name)

        identifier = cls.get_chain_identifier(extended.chains[0].info) if extended.chains else None

        # Get plex identifier
        season = try_convert(video.get('parentIndex'), int)
        episode = try_convert(video.get('index'), int)

        # Ensure season and episode numbers are valid
        if season is None or episode is None:
            log.debug('Ignoring item with key "%s", invalid season or episode attribute', video.get('ratingKey'))
            return None, []

        if identifier:
            # Ensure extended season matches plex
            if identifier.get('season') != season:
                log.debug(IDENTIFIER_MISMATCH, file_name, 'season: extended %s !=  plex %s' % (identifier.get('season'), season))
                return season, [episode]

            # Ensure extended single episode matches plex
            if 'episode' in identifier:
                episodes = identifier['episode']

                if not isinstance(episodes, list):
                    episodes = [episodes]

                if episode not in episodes:
                    log.debug(IDENTIFIER_MISMATCH, file_name, 'episode: extended %s does not contain plex %s' % (episodes, episode))

                return season, episodes

            if 'episode_from' in identifier and 'episode_to' in identifier:
                episodes = range(identifier.get('episode_from'), identifier.get('episode_to') + 1)

                # Ensure plex episode is inside extended episode range
                if episode not in episodes:
                    log.debug(IDENTIFIER_MISMATCH, file_name, 'episode: extended %s does not contain plex %s' %(episodes, episode))
                    return season, [episode]

                return season, episodes


        return season, [episode]



    # TODO move to plex.metadata, cache results
    @classmethod
    def get_episodes(cls, key, parent=None, cache_id=None):
        """Fetch the episodes for a show from the Plex library

        :param key: Key of show to fetch episodes for
        :type key: str

        :param cache_id: Cached response identifier
        :type cache_id: str

        :return: Dictionary containing the episodes in this form: {season_num: {episode_num: <PlexEpisode>}}
        :rtype: dict
        """

        result = {}

        container = cls.request('library/metadata/%s/allLeaves' % key, timeout=10, cache_id=cache_id)

        for video in container:
            season, episodes = cls.get_episode_identifier(video)

            for episode in episodes:
                result[season, episode] = PlexEpisode.create(parent, video, season, episode)

        return result

    @classmethod
    def scrobble(cls, key):
        result = cls.request(
            ':/scrobble?identifier=com.plexapp.plugins.library&key=%s' % key,
            response_type='text'
        )

        return result is not None

    @classmethod
    def rate(cls, key, value):
        result = cls.request(
            ':/rate?key=%s&identifier=com.plexapp.plugins.library&rating=%s' % (key, value),
            response_type='text'
        )

        return result is not None
