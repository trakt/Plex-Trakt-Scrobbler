from plex_metadata.core.helpers import try_convert
import plex.lib.six.moves.urllib_parse as urlparse

import logging
import re

DEFAULT_MEDIA = ['movie', 'show', 'season', 'episode']

log = logging.getLogger(__name__)


class Agent(object):
    def __init__(self, media, service, regex=None, type=None, children=None, season=None):
        self.media = media
        self.service = service

        self.regex = regex
        self.type = type

        self.children = children

        self.season = season

    #
    # Compile
    #

    @classmethod
    def compile(cls, entry, media=None):
        # Construct `Agent`
        return cls(
            media=cls.get_media(entry, media),
            service=entry.get('service'),
            type=entry.get('type'),

            # Compile regular expression
            regex=cls.compile_pattern(entry.get('pattern')),

            # Compile children
            children=[
                cls.compile(child, media)
                for child in (entry.get('children') or [])
            ],

            # Overrides
            season=entry.get('season')
        )

    @staticmethod
    def compile_pattern(pattern):
        if pattern is None:
            return None

        try:
            return re.compile(pattern, re.IGNORECASE)
        except Exception as ex:
            log.warn('Unable to compile regular expression: %r - %s', pattern, ex, exc_info=True)

        return None

    @staticmethod
    def get_media(entry, media=None):
        if entry.get('media') is None:
            return DEFAULT_MEDIA

        return entry.get('media') + (media or [])

    #
    # Fill
    #

    def fill(self, guid, uri, media=None):
        # Validate media matches agent
        if media is not None and media not in self.media:
            return False

        # Search children for match
        if self.children:
            # Iterate over children, checking if `guid` can be filled
            for child in self.children:
                if child.fill(guid, uri, media):
                    return True

        # Parse netloc (media id)
        if self.regex:
            # Match `uri.netloc` against pattern
            match = self.regex.match(uri.netloc)

            if not match:
                return False

            id = ''.join(match.groups())
        else:
            id = uri.netloc

        # Cast `id` to defined type
        if self.type:
            id = try_convert(id, self.type, id)

        # Update `guid`
        guid.service = self.service or guid.agent_id
        guid.id = id

        # Fill `guid` with extra details from URI
        self.fill_path(guid, uri.path)
        self.fill_query(guid, uri.query)

        # Process overrides
        if self.season is not None:
            guid.season = self.season

        return True

    def fill_path(self, guid, path):
        # Split path into fragments
        fragments = path.strip('/').split('/')

        # Retrieve TV parameters
        if 'season' in self.media and len(fragments) >= 1:
            guid.season = try_convert(fragments[0], int)

        if 'episode' in self.media and len(fragments) >= 2:
            guid.episode = try_convert(fragments[1], int)

    @staticmethod
    def fill_query(guid, query):
        # Parse query parameters
        parameters = dict(urlparse.parse_qsl(query))

        # Update `guid` with parameters
        guid.language = parameters.get('lang')
