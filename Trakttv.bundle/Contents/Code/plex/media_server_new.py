from core.helpers import all, try_convert
from core.logger import Logger
from plex.metadata import PlexMetadata
from plex.plex_base import PlexBase
from plex.plex_objects import PlexShow, PlexEpisode

log = Logger('plex.media_server_new')


class PlexMediaServer(PlexBase):
    @classmethod
    def get_sections(cls, types=None, keys=None, cache_id=None):
        """Get the current sections available on the server, optionally
        filtering by type and/or key

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
        return cls.request('library/sections/%s/all' % key, cache_id=cache_id)

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
    def get_library_key(cls, key):
        parsed_guid = PlexMetadata.get_parsed_guid(key=key)

        log.debug('get_library_key key: %s, parsed_guid: %s', key, parsed_guid)

        # Ensure service id is valid
        if not parsed_guid.sid:
            log.warn('Missing service identifier for movie with ratingKey "%s"', key)
            return None, None

        agent = parsed_guid.agent
        return parsed_guid, (agent[agent.rfind('.') + 1:], parsed_guid.sid)

    @classmethod
    def get_library(cls, types=None, keys=None, cache_id=None):
        # Get all sections or filter based on 'types' and 'sections'
        sections = [(type, key) for (type, key, _) in cls.get_sections(types, keys, cache_id=cache_id)]

        movies = {}
        shows = {}

        for type, key in sections:
            if type == 'movie':
                for video in cls.get_videos(key, cache_id=cache_id):
                    parsed_guid, key = cls.get_library_key(video.get('ratingKey'))
                    if parsed_guid is None:
                        continue

                    if key not in shows:
                        movies[key] = []

                    movies[key].append(PlexShow.create(video, parsed_guid))

            if type == 'show':
                for directory in cls.get_directories(key, cache_id=cache_id):
                    parsed_guid, key = cls.get_library_key(directory.get('ratingKey'))
                    if parsed_guid is None:
                        continue

                    if key not in shows:
                        shows[key] = []

                    shows[key].append(PlexShow.create(directory, parsed_guid))

        log.debug('movies: %s', movies)
        log.debug('shows: %s', shows)

        return movies, shows

    @classmethod
    def get_episodes(cls, key, cache_id=None):
        result = {}  # {season_num: {episode_num: <PlexEpisode>}}

        container = cls.request('library/metadata/%s/allLeaves' % key, cache_id=cache_id)

        for video in container:
            season = try_convert(video.get('parentIndex'), int)
            episode = try_convert(video.get('index'), int)

            # Ensure season and episode numbers are valid
            if season is None or episode is None:
                log.warn('Ignoring item with key "%s", invalid season or episode attribute', video.get('ratingKey'))
                continue

            if season not in result:
                result[season] = {}

            result[season][episode] = PlexEpisode.create(video, season, episode)

        return result
