from core.helpers import build_repr, try_convert
from core.logger import Logger
from urlparse import urlparse

SHOW_AGENTS = [
    'com.plexapp.agents.thetvdb',
    'com.plexapp.agents.thetvdbdvdorder',
    'com.plexapp.agents.abstvdb',
    'com.plexapp.agents.xbmcnfotv',
    'com.plexapp.agents.mcm'
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
        path_fragments = uri.path.strip('/').split('/')

        if agent in SHOW_AGENTS:
            if len(path_fragments) >= 1:
                result.season = try_convert(path_fragments[0], int)

            if len(path_fragments) >= 2:
                result.episode = try_convert(path_fragments[1], int)
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

        self.type = None

        self.title = None
        self.year = None

        self.agent = None
        self.sid = None

        self.user_rating = None

        self.section_key = None
        self.section_title = None

    @staticmethod
    def fill(obj, container, video, parsed_guid=None):
        obj.type = video.get('type')

        obj.title = video.get('title')
        obj.year = try_convert(video.get('year'), int)

        obj.user_rating = try_convert(video.get('userRating'), float)

        if obj.user_rating:
            obj.user_rating = int(round(obj.user_rating, 0))

        obj.section_key = try_convert(container.get('librarySectionID'), int)
        obj.section_title = container.get('librarySectionTitle')

        if parsed_guid is not None:
            obj.agent = parsed_guid.agent
            obj.sid = parsed_guid.sid

    @staticmethod
    def get_repr_keys():
        return [
            'rating_key', 'key',
            'type',
            'title', 'year',
            'agent', 'sid',
            'user_rating',
            'section_key', 'section_title'
        ]

    def to_dict(self):
        items = []

        for key in self.get_repr_keys():
            value = getattr(self, key)

            if isinstance(value, PlexMedia):
                value = value.to_dict()

            items.append((key, value))

        return dict(items)

    def __repr__(self):
        return build_repr(self, self.get_repr_keys() or [])

    def __str__(self):
        return self.__repr__()


class PlexVideo(PlexMedia):
    def __init__(self, rating_key, key=None):
        super(PlexVideo, self).__init__(rating_key, key)

        self.view_count = 0
        self.duration = None

    @property
    def seen(self):
        return self.view_count and self.view_count > 0

    @staticmethod
    def fill(obj, container, video, parsed_guid=None):
        PlexMedia.fill(obj, container, video, parsed_guid)

        obj.view_count = try_convert(video.get('viewCount'), int)
        obj.duration = try_convert(video.get('duration'), int, 0) / float(1000 * 60)  # Convert to minutes

    @staticmethod
    def get_repr_keys():
        return PlexMedia.get_repr_keys() + ['view_count', 'duration']


class PlexShow(PlexMedia):
    def __init__(self, rating_key, key):
        super(PlexShow, self).__init__(rating_key, key)

    @classmethod
    def create(cls, container, directory, parsed_guid, key):
        if parsed_guid.season or parsed_guid.episode:
            raise ValueError('parsed_guid is not valid for PlexShow')

        show = cls(directory.get('ratingKey'), key)

        cls.fill(show, container, directory, parsed_guid)
        return show


class PlexEpisode(PlexVideo):
    def __init__(self, parent, rating_key, key):
        super(PlexEpisode, self).__init__(rating_key, key)

        self.parent = parent

        self.grandparent_title = None

        self.season = None
        self.episodes = None

    @classmethod
    def create(cls, container, video, season, episodes, parsed_guid=None, key=None, parent=None):
        obj = cls(parent, video.get('ratingKey'), key)

        obj.grandparent_title = video.get('grandparentTitle')

        obj.season = season
        obj.episodes = episodes

        cls.fill(obj, container, video, parsed_guid)
        return obj

    @staticmethod
    def get_repr_keys():
        return PlexVideo.get_repr_keys() + ['parent', 'grandparent_title', 'season', 'episodes']


class PlexMovie(PlexVideo):
    def __init__(self, rating_key, key):
        super(PlexMovie, self).__init__(rating_key, key)

    @classmethod
    def create(cls, container, video, parsed_guid, key):
        if parsed_guid.season or parsed_guid.episode:
            raise ValueError('parsed_guid is not valid for PlexShow')

        movie = cls(video.get('ratingKey'), key)

        cls.fill(movie, container, video, parsed_guid)
        return movie
