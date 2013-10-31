from core.helpers import add_attribute
from core.http import responses


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


class PlexMediaServer(object):
    base_url = 'http://localhost:32400'

    @classmethod
    def request(cls, path, data_type='xml', method='GET'):
        if not path.startswith('/'):
            path = '/' + path

        url = cls.base_url + path

        if data_type == 'xml':
            return XML.ElementFromURL(url, errors='ignore')

        if data_type == 'text':
            return HTTP.Request(url, method=method)

        raise ValueError()

    @classmethod
    def add_guid(cls, metadata, section):
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
    def metadata(cls, item_id):
        # Prepare a dict that contains all the metadata required for trakt.
        try:
            xml_content = cls.request('library/metadata/%s' % item_id).xpath('//Video')

            for section in xml_content:
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

            Log.Debug('xml_content = %s' % xml_content)
            Log.Warn('Unable to find metadata for item %s' % item_id)
        except Ex.HTTPError, e:
            Log.Debug(str(e))
            Log.Warn('Network error while fetching metadata, Failed to connect to %s.' % cls.base_url)
        except Ex.URLError, e:
            Log.Debug(str(e))
            Log.Warn('Network error while fetching metadata, Failed to connect to %s.' % cls.base_url)

        return None

    @classmethod
    def client(cls, client_id):
        if not client_id:
            Log.Warn('Invalid client_id provided')
            return None

        xml_content = cls.request('clients').xpath('//Server')

        found_clients = []

        for section in xml_content:
            found_clients.append(section.get('machineIdentifier'))

            if section.get('machineIdentifier') == client_id:
                return section

        Log.Warn("Unable to find client '%s', available clients: %s" % (client_id, found_clients))
        return None

    @classmethod
    def set_logging_state(cls, state):
        try:
            response = cls.request(':/prefs?logDebug=%s' % int(state), data_type='text', method='PUT')
            Log.Debug('Response: %s' % (response.content if response else None))
            return True
        except Ex.HTTPError:
            pass
        except Ex.URLError:
            pass

        return False

    @classmethod
    def get_logging_state(cls):
        for setting in cls.request(':/prefs').xpath('//Setting'):

            if setting.get('id') == 'logDebug' and setting.get('value'):
                value = setting.get('value').lower()
                return True if value == 'true' else False

        Log.Warn('Unable to determine logging state, assuming disabled')
        return False
