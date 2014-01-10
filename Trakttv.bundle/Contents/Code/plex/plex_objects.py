from core.helpers import build_repr
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
    def __init__(self, rating_key):
        self.rating_key = rating_key

        self.agent = None
        self.sid = None


class PlexShow(PlexMedia):
    def __init__(self, rating_key):
        super(PlexShow, self).__init__(rating_key)

    @classmethod
    def create(cls, directory, parsed_guid):
        if parsed_guid.season or parsed_guid.episode:
            raise ValueError('parsed_guid is not valid for PlexShow')

        show = cls(directory.get('ratingKey'))
        show.agent = parsed_guid.agent
        show.sid = parsed_guid.sid

        return show

    def __repr__(self):
        return build_repr(self, ['agent', 'sid'])

    def __str__(self):
        return self.__repr__()


class PlexMovie(PlexMedia):
    def __init__(self, rating_key):
        super(PlexMovie, self).__init__(rating_key)
