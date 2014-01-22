from core.helpers import build_repr, try_convert
from core.logger import Logger
from urlparse import urlparse

SHOW_AGENTS = [
    'com.plexapp.agents.thetvdb',
    'com.plexapp.agents.abstvdb',
    'com.plexapp.agents.xbmcnfotv',
]

log = Logger('plex.plex_objects')


class PlexParsedGuid(object):
    def __init__(self, agent, sid, extra):
        self.agent = agent
        self.sid = sid
        self.extra = extra

        # Show
        self.season = None
        self.episode = None


    @classmethod
    def from_guid(cls, guid):
        if not guid:
            return None

        uri = urlparse(guid)
        agent = uri.scheme

        result = PlexParsedGuid(agent, uri.netloc, uri.query)

        # Nothing more to parse, return now
        if not uri.path:
            return result

        # Parse path component for agent-specific data
        path_fragments = uri.path.split('/')

        if agent in SHOW_AGENTS:
            if len(path_fragments) >= 1:
                result.season = path_fragments[0]

            if len(path_fragments) >= 2:
                result.episode = path_fragments[1]
        else:
            log.warn('Unable to completely parse guid "%s"', guid)

        return result

    def __repr__(self):
        return build_repr(self, ['agent', 'sid', 'extra', 'season', 'episode'])

    def __str__(self):
        return self.__repr__()


class PlexMedia(object):
    def __init__(self, rating_key, key=None):
        self.rating_key = rating_key
        self.key = key

        self.title = None
        self.year = None

        self.agent = None
        self.sid = None

        self.user_rating = None

    @staticmethod
    def fill(obj, video, parsed_guid=None):
        obj.title = video.get('title')
        obj.year = try_convert(video.get('year'), int)

        obj.user_rating = try_convert(video.get('userRating'), int)

        if parsed_guid is not None:
            obj.agent = parsed_guid.agent
            obj.sid = parsed_guid.sid

    @staticmethod
    def get_repr_keys():
        return ['rating_key', 'key', 'title', 'agent', 'sid', 'user_rating']

    def __repr__(self):
        return build_repr(self, self.get_repr_keys() or [])

    def __str__(self):
        return self.__repr__()


class PlexVideo(PlexMedia):
    def __init__(self, rating_key, key=None):
        super(PlexVideo, self).__init__(rating_key, key)

        self.view_count = 0

    @property
    def seen(self):
        return self.view_count and self.view_count > 0

    @staticmethod
    def fill(obj, video, parsed_guid=None):
        PlexMedia.fill(obj, video, parsed_guid)

        obj.view_count = try_convert(video.get('viewCount'), int)

    @staticmethod
    def get_repr_keys():
        return PlexMedia.get_repr_keys() + ['view_count']


class PlexShow(PlexMedia):
    def __init__(self, rating_key, key):
        super(PlexShow, self).__init__(rating_key, key)

    @classmethod
    def create(cls, directory, parsed_guid, key):
        if parsed_guid.season or parsed_guid.episode:
            raise ValueError('parsed_guid is not valid for PlexShow')

        show = cls(directory.get('ratingKey'), key)

        cls.fill(show, directory, parsed_guid)
        return show


class PlexEpisode(PlexVideo):
    def __init__(self, parent, rating_key):
        super(PlexEpisode, self).__init__(rating_key)

        self.parent = parent

        self.season_num = None
        self.episode_num = None

    @classmethod
    def create(cls, parent, video, season_num, episode_num):
        if season_num is None or episode_num is None:
            raise ValueError('season_num and episode_num required for PlexEpisode')

        episode = cls(parent, video.get('ratingKey'))
        episode.season_num = season_num
        episode.episode_num = episode_num

        cls.fill(episode, video)
        return episode

    @staticmethod
    def get_repr_keys():
        return PlexVideo.get_repr_keys() + ['parent', 'season_num', 'episode_num']


class PlexMovie(PlexVideo):
    def __init__(self, rating_key, key):
        super(PlexMovie, self).__init__(rating_key, key)

    @classmethod
    def create(cls, video, parsed_guid, key):
        if parsed_guid.season or parsed_guid.episode:
            raise ValueError('parsed_guid is not valid for PlexShow')

        movie = cls(video.get('ratingKey'), key)

        cls.fill(movie, video, parsed_guid)
        return movie
