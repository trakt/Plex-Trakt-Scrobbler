from core.logger import Logger
from plex.plex_base import PlexBase
from plex.plex_objects import PlexShow, PlexEpisode, PlexMovie
from plex.plex_matcher import PlexMatcher
from plex.plex_metadata import PlexMetadata
from plex.plex_media_server import PlexMediaServer

log = Logger('plex.plex_library')


class PlexLibrary(PlexBase):
    @classmethod
    def map_item(cls, table, container, media):
        # Get the key for the item
        parsed_guid, key = PlexMetadata.get_key(media.get('ratingKey'))
        if parsed_guid is None:
            return False

        if key not in table:
            table[key] = []

        # Create object for the data
        data_type = media.get('type')
        if data_type == 'movie':
            item = PlexMovie.create(container, media, parsed_guid, key)
        elif data_type == 'show':
            item = PlexShow.create(container, media, parsed_guid, key)
        else:
            log.info('Unknown item "%s" with type "%s"', media.get('ratingKey'), data_type)
            return False

        # Map item into table
        table[key].append(item)
        return True

    @classmethod
    def fetch(cls, types=None, keys=None, titles=None, cache_id=None):
        if types and isinstance(types, basestring):
            types = [types]

        # Get all sections or filter based on 'types' and 'sections'
        sections = [(type, key) for (type, key, _) in PlexMediaServer.get_sections(
            types, keys, titles,
            cache_id=cache_id
        )]

        movies = {}
        shows = {}

        for type, key in sections:
            container = PlexMediaServer.get_section(key, cache_id=cache_id)
            if container is None:
                continue

            for media in container:
                if type == 'movie':
                    cls.map_item(movies, container, media)

                if type == 'show':
                    cls.map_item(shows, container, media)

        if len(types) == 1:
            if types[0] == 'movie':
                return movies

            if types[0] == 'show':
                return shows

        return movies, shows

    @classmethod
    def fetch_episodes(cls, key, parent=None, cache_id=None):
        """Fetch the episodes for a show from the Plex library

        :param key: Key of show to fetch episodes for
        :type key: str

        :param cache_id: Cached response identifier
        :type cache_id: str

        :return: Dictionary containing the episodes in this form: {season_num: {episode_num: <PlexEpisode>}}
        :rtype: dict
        """

        result = {}

        container = cls.request(
            'library/metadata/%s/allLeaves' % key,
            timeout=30, max_retries=2, retry_sleep=2,
            cache_id=cache_id
        )

        if container is None:
            log.warn('Unable to retrieve episodes (key: "%s")', key)
            return None

        for video in container:
            season, episodes = PlexMatcher.get_identifier(video)

            obj = PlexEpisode.create(container, video, season, episodes, parent=parent)

            for episode in episodes:
                result[season, episode] = obj

        # Ensure PlexMatcher cache is stored to disk
        PlexMatcher.save()

        return result
