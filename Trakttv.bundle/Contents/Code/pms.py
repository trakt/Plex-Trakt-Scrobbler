from helpers import add_attribute
from http import responses

# Regular Expressions for GUID parsing
MOVIE_REGEXP = Regex('com.plexapp.agents.*://(?P<imdb_id>tt[-a-z0-9\.]+)')
MOVIEDB_REGEXP = Regex('com.plexapp.agents.themoviedb://(?P<tmdb_id>[0-9]+)')
STANDALONE_REGEXP = Regex('com.plexapp.agents.standalone://(?P<tmdb_id>[0-9]+)')

TVSHOW_REGEXP = Regex('com.plexapp.agents.thetvdb://(?P<tvdb_id>[-a-z0-9\.]+)/'
                      '(?P<season>[-a-z0-9\.]+)/(?P<episode>[-a-z0-9\.]+)')
TVSHOW1_REGEXP = Regex('com.plexapp.agents.thetvdb://([-a-z0-9\.]+)')

MOVIE_PATTERNS = [
    MOVIE_REGEXP,
    MOVIEDB_REGEXP,
    STANDALONE_REGEXP
]

PMS_URL = 'http://localhost:32400/library/%s'


def add_guid(metadata, section):
    guid = section.get('guid')

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


@route('/applications/trakttv/get_metadata_from_pms')
def get_metadata_from_pms(item_id):
    # Prepare a dict that contains all the metadata required for trakt.
    pms_url = PMS_URL % ('metadata/' + str(item_id))

    try:
        xml_content = XML.ElementFromString(HTTP.Request(pms_url)).xpath('//Video')

        for section in xml_content:
            metadata = {'title': section.get('title')}

            # Add attributes if they exist
            add_attribute(metadata, section, 'duration', float, lambda x: int(x / 60000))
            add_attribute(metadata, section, 'year', int)

            # Add guid match data
            add_guid(metadata, section)

            return metadata

    except Ex.HTTPError, e:
        Log('Failed to connect to %s.' % pms_url)
        return {'status': False, 'message': responses[e.code][1]}
    except Ex.URLError, e:
        Log('Failed to connect to %s.' % pms_url)
        return {'status': False, 'message': e.reason[0]}
