from core.helpers import add_attribute
from core.network import request


# Regular Expressions for GUID parsing
MOVIE_REGEXP = Regex('com.plexapp.agents.*://(?P<imdb_id>tt[-a-z0-9\.]+)')
MOVIEDB_REGEXP = Regex('com.plexapp.agents.themoviedb://(?P<tmdb_id>[0-9]+)')
STANDALONE_REGEXP = Regex('com.plexapp.agents.standalone://(?P<tmdb_id>[0-9]+)')

TVSHOW_REGEXP = Regex('com.plexapp.agents.(thetvdb|abstvdb|xbmcnfotv)://(?P<tvdb_id>[-a-z0-9\.]+)/'
                      '(?P<season>[-a-z0-9\.]+)/(?P<episode>[-a-z0-9\.]+)')
TVSHOW1_REGEXP = Regex('com.plexapp.agents.(thetvdb|abstvdb|xbmcnfotv)://([-a-z0-9\.]+)')

MOVIE_PATTERNS = [
    MOVIE_REGEXP,
    MOVIEDB_REGEXP,
    STANDALONE_REGEXP
]

PMS_URL = 'http://localhost:32400%s'  # TODO remove this, replace with PMS.base_url


class PMS(object):
    base_url = 'http://localhost:32400'

    @classmethod
    def request(cls, path='/', response_type='xml', raise_exceptions=False, retry=True, timeout=3):
        if not path.startswith('/'):
            path = '/' + path

        return request(
            cls.base_url + path,
            response_type,

            raise_exceptions=raise_exceptions,

            retry=retry,
            timeout=timeout
        )

    @classmethod
    def metadata(cls, item_id):
        # Prepare a dict that contains all the metadata required for trakt.
        response = cls.request('library/metadata/%s' % item_id)
        if not response:
            return None

        for section in response.data.xpath('//Video'):
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

        response = cls.request('clients')
        if not response:
            return None

        found_clients = []

        for section in response.data.xpath('//Server'):
            found_clients.append(section.get('machineIdentifier'))

            if section.get('machineIdentifier') == client_id:
                return section

        Log.Info("Unable to find client '%s', available clients: %s" % (client_id, found_clients))
        return None

    @classmethod
    def set_logging_state(cls, state):
        # TODO PUT METHOD
        response = cls.request(':/prefs?logDebug=%s' % int(state), 'text', method='PUT')
        if not response:
            return False

        Log.Debug('Response: %s' % (response.data if response else None))
        return True

    @classmethod
    def get_logging_state(cls):
        response = cls.request(':/prefs')
        if not response:
            return False

        for setting in response.data.xpath('//Setting'):

            if setting.get('id') == 'logDebug' and setting.get('value'):
                value = setting.get('value').lower()
                return True if value == 'true' else False

        Log.Warn('Unable to determine logging state, assuming disabled')
        return False

    @classmethod
    def get_server_info(cls):
        response = request(PMS_URL % '', 'xml')
        if not response:
            return None

        return response.data

    @classmethod
    def get_server_version(cls, default=None):
        server_info = cls.get_server_info()
        if not server_info:
            return default

        return server_info.attrib.get('version') or default

    @classmethod
    def get_status(cls):
        response = request(PMS_URL % '/status/sessions', 'xml')
        if not response:
            return None

        return response.data

    @classmethod
    def get_video_session(cls, session_key):
        status = cls.get_status()
        if not status:
            Log.Warn('Status request failed, unable to connect to server')
            return None

        for section in status.xpath('//MediaContainer/Video'):
            if section.get('sessionKey') == session_key and '/library/metadata' in section.get('key'):
                return section

        Log.Warn('Session not found')
        return None

    @classmethod
    def get_metadata(cls, key):
        response = request(PMS_URL % ('/library/metadata/%s' % key), 'xml')
        if not response:
            return None

        return response.data

    @classmethod
    def get_metadata_guid(cls, key):
        metadata = cls.get_metadata(key)
        if not metadata:
            return None

        return metadata.xpath('//Directory')[0].get('guid')

    @classmethod
    def get_metadata_leaves(cls, key):
        response = request(PMS_URL % ('/library/metadata/%s/allLeaves' % key), 'xml')
        if not response:
            return None

        return response.data

    @classmethod
    def get_sections(cls):
        response = request(PMS_URL % '/library/sections', 'xml')
        if not response:
            return None

        return response.data

    @classmethod
    def get_section(cls, name):
        response = request(PMS_URL % ('/library/sections/%s/all' % name), 'xml')
        if not response:
            return None

        return response.data

    @classmethod
    def get_section_directories(cls, section_name):
        section = cls.get_section(section_name)
        if not section:
            return None

        return section.xpath('//Directory')

    @classmethod
    def get_section_videos(cls, section_name):
        section = cls.get_metadata(section_name)
        if not section:
            return None

        return section.xpath('//Video')

    @classmethod
    def scrobble(cls, video):
        if video.get('viewCount') > 0:
            Log('video has already been marked as seen')
            return False

        response = request(PMS_URL % '/:/scrobble?identifier=com.plexapp.plugins.library&key=%s' % (
            video.get('ratingKey')
        ))

        return response is not None

    @classmethod
    def rate(cls, video, rating):
        response = request(PMS_URL % '/:/rate?key=%s&identifier=com.plexapp.plugins.library&rating=%s' % (
            video.get('ratingKey'), rating
        ))

        return response is not None
