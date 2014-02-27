from core.helpers import add_attribute
from core.network import request


# Regular Expressions for GUID parsing
MOVIE_REGEXP = Regex('com.plexapp.agents.*://(?P<imdb_id>tt[-a-z0-9\.]+)')
MOVIEDB_REGEXP = Regex('com.plexapp.agents.themoviedb://(?P<tmdb_id>[0-9]+)')
STANDALONE_REGEXP = Regex('com.plexapp.agents.standalone://(?P<tmdb_id>[0-9]+)')

TVSHOW_REGEXP = Regex(
    'com.plexapp.agents.(thetvdb|thetvdbdvdorder|abstvdb|xbmcnfotv|mcm)://'
    '(MCM_TV_A_)?'  # For Media Center Master
    '(?P<tvdb_id>[-a-z0-9\.]+)/'
    '(?P<season>[-a-z0-9\.]+)/'
    '(?P<episode>[-a-z0-9\.]+)'
)

TVSHOW1_REGEXP = Regex(
    'com.plexapp.agents.(thetvdb|thetvdbdvdorder|abstvdb|xbmcnfotv|mcm)://'
    '(MCM_TV_A_)?'  # For Media Center Master
    '(?P<tvdb_id>[-a-z0-9\.]+)'
)

MOVIE_PATTERNS = [
    MOVIE_REGEXP,
    MOVIEDB_REGEXP,
    STANDALONE_REGEXP
]


class PMS(object):
    base_url = 'http://127.0.0.1:32400'

    @classmethod
    def request(cls, path='/', response_type='xml', raise_exceptions=False, retry=True, timeout=3, **kwargs):
        if not path.startswith('/'):
            path = '/' + path

        response = request(
            cls.base_url + path,
            response_type,

            raise_exceptions=raise_exceptions,

            retry=retry,
            timeout=timeout,

            **kwargs
        )

        return response.data if response else None

    @classmethod
    def metadata(cls, item_id):
        # Prepare a dict that contains all the metadata required for trakt.
        result = cls.request('library/metadata/%s' % item_id)
        if not result:
            return None

        for section in result.xpath('//Video'):
            metadata = {}

            # Add attributes if they exist
            add_attribute(metadata, section, 'duration', float, lambda x: int(x / 60000))
            add_attribute(metadata, section, 'year', int)

            add_attribute(metadata, section, 'lastViewedAt', int, target_key='last_played')
            add_attribute(metadata, section, 'viewCount', int, target_key='plays')

            add_attribute(metadata, section, 'type')

            if metadata['type'] == 'movie':
                metadata['title'] = section.get('title')

            elif metadata['type'] == 'episode':
                metadata['title'] = section.get('grandparentTitle')
                metadata['episode_title'] = section.get('title')

            # Add guid match data
            cls.add_guid(metadata, section)

            return metadata

        Log.Warn('Unable to find metadata for item %s' % item_id)
        return None

    @staticmethod
    def add_guid(metadata, section):
        guid = section.get('guid')
        if not guid:
            return

        if section.get('type') == 'movie':

            # Cycle through patterns and try get a result
            for pattern in MOVIE_PATTERNS:
                match = pattern.search(guid)

                # If we have a match, update the metadata
                if match:
                    metadata.update(match.groupdict())
                    return

            Log('The movie %s doesn\'t have any imdb or tmdb id, it will be ignored.' % section.get('title'))
        elif section.get('type') == 'episode':
            match = TVSHOW_REGEXP.search(guid)

            # If we have a match, update the metadata
            if match:
                metadata.update(match.groupdict())
            else:
                Log('The episode %s doesn\'t have any tmdb id, it will not be scrobbled.' % section.get('title'))
        else:
            Log('The content type %s is not supported, the item %s will not be scrobbled.' % (
                section.get('type'), section.get('title')
            ))

    @classmethod
    def client(cls, client_id):
        if not client_id:
            Log.Warn('Invalid client_id provided')
            return None

        result = cls.request('clients')
        if not result:
            return None

        found_clients = []

        for section in result.xpath('//Server'):
            found_clients.append(section.get('machineIdentifier'))

            if section.get('machineIdentifier') == client_id:
                return section

        Log.Info("Unable to find client '%s', available clients: %s" % (client_id, found_clients))
        return None

    @classmethod
    def get_server_info(cls):
        return cls.request()

    @classmethod
    def get_server_version(cls, default=None):
        server_info = cls.get_server_info()
        if server_info is None:
            return default

        return server_info.attrib.get('version') or default

    @classmethod
    def get_sessions(cls):
        return cls.request('status/sessions')

    @classmethod
    def get_video_session(cls, session_key):
        sessions = cls.get_sessions()
        if sessions is None:
            Log.Warn('Status request failed, unable to connect to server')
            return None

        for section in sessions.xpath('//MediaContainer/Video'):
            if section.get('sessionKey') == session_key and '/library/metadata' in section.get('key'):
                return section

        Log.Warn('Session not found')
        return None

    @classmethod
    def get_metadata(cls, key):
        return cls.request('library/metadata/%s' % key)

    @classmethod
    def get_metadata_guid(cls, key):
        metadata = cls.get_metadata(key)
        if metadata is None:
            return None

        return metadata.xpath('//Directory')[0].get('guid')

    @classmethod
    def get_metadata_leaves(cls, key):
        return cls.request('library/metadata/%s/allLeaves' % key, timeout=10)

    @classmethod
    def get_sections(cls):
        return cls.request('library/sections')

    @classmethod
    def get_section(cls, name):
        return cls.request('library/sections/%s/all' % name, timeout=10)

    @classmethod
    def get_section_directories(cls, section_name):
        section = cls.get_section(section_name)
        if section is None:
            return []

        return section.xpath('//Directory')

    @classmethod
    def get_section_videos(cls, section_name):
        section = cls.get_section(section_name)
        if section is None:
            return []

        return section.xpath('//Video')

    @classmethod
    def scrobble(cls, video):
        if video.get('viewCount') > 0:
            Log.Debug('video has already been marked as seen')
            return False

        result = cls.request(
            ':/scrobble?identifier=com.plexapp.plugins.library&key=%s' % (
                video.get('ratingKey')
            ),
            response_type='text'
        )

        return result is not None

    @classmethod
    def rate(cls, video, rating):
        result = cls.request(
            ':/rate?key=%s&identifier=com.plexapp.plugins.library&rating=%s' % (
                video.get('ratingKey'), rating
            ),
            response_type='text'
        )

        return result is not None
