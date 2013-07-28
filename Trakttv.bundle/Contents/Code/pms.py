from http import responses

#Regexps to load data from strings
LOG_REGEXP = Regex('(?P<key>\w*?)=(?P<value>\w+\w?)')
MOVIE_REGEXP = Regex('com.plexapp.agents.*://(tt[-a-z0-9\.]+)')
MOVIEDB_REGEXP = Regex('com.plexapp.agents.themoviedb://([0-9]+)')
STANDALONE_REGEXP = Regex('com.plexapp.agents.standalone://([0-9]+)')
TVSHOW_REGEXP = Regex('com.plexapp.agents.thetvdb://([-a-z0-9\.]+)/([-a-z0-9\.]+)/([-a-z0-9\.]+)')
TVSHOW1_REGEXP = Regex('com.plexapp.agents.thetvdb://([-a-z0-9\.]+)')

PMS_URL = 'http://localhost:32400/library/%s'

@route('/applications/trakttv/get_metadata_from_pms')
def get_metadata_from_pms(item_id):
    # Prepare a dict that contains all the metadata required for trakt.
    pms_url = PMS_URL % ('metadata/' + str(item_id))

    try:
        xml_file = HTTP.Request(pms_url)
        xml_content = XML.ElementFromString(xml_file).xpath('//Video')
        for section in xml_content:
            metadata = {'title' : section.get('title')}

            try:
                metadata['duration'] = int(float(section.get('duration')) / 60000)
            except: pass

            if section.get('year') is not None:
                metadata['year'] = int(section.get('year'))

            if section.get('type') == 'movie':
                try:
                    metadata['imdb_id'] = MOVIE_REGEXP.search(section.get('guid')).group(1)
                except:
                    try:
                        metadata['tmdb_id'] = MOVIEDB_REGEXP.search(section.get('guid')).group(1)
                    except:
                        try:
                            metadata['tmdb_id'] = STANDALONE_REGEXP.search(section.get('guid')).group(1)
                        except:
                            Log('The movie %s doesn\'t have any imdb or tmdb id, it will be ignored.' % section.get('title'))
            elif section.get('type') == 'episode':
                try:
                    m = TVSHOW_REGEXP.search(section.get('guid'))
                    metadata['tvdb_id'] = m.group(1)
                    metadata['season'] = m.group(2)
                    metadata['episode'] = m.group(3)
                except:
                    Log('The episode %s doesn\'t have any tmdb id, it will not be scrobbled.' % section.get('title'))
            else:
                Log('The content type %s is not supported, the item %s will not be scrobbled.' % (section.get('type'), section.get('title')))

            return metadata
    except Ex.HTTPError, e:
        Log('Failed to connect to %s.' % pms_url)
        return {'status': False, 'message': responses[e.code][1]}
    except Ex.URLError, e:
        Log('Failed to connect to %s.' % pms_url)
        return {'status': False, 'message': e.reason[0]}
