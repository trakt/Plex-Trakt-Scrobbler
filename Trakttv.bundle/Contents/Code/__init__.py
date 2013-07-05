import time
import websocket
import ast

NAME = L('Title')
ART  = 'art-default.jpg'
ICON = 'icon-default.png'
PMS_URL = 'http://localhost:32400%s'
TRAKT_URL = 'http://api.trakt.tv/%s/ba5aa61249c02dc5406232da20f6e768f3c82b28%s'
PLUGIN_VERSION = '0.6'

#Regexps to load data from strings
MOVIE_REGEXP = Regex('com.plexapp.agents.*://(tt[-a-z0-9\.]+)')
MOVIEDB_REGEXP = Regex('com.plexapp.agents.themoviedb://([0-9]+)')
STANDALONE_REGEXP = Regex('com.plexapp.agents.standalone://([0-9]+)')
TVSHOW_REGEXP = Regex('com.plexapp.agents.(thetvdb|abstvdb)://([-a-z0-9\.]+)/([-a-z0-9\.]+)/([-a-z0-9\.]+)')
TVSHOW1_REGEXP = Regex('com.plexapp.agents.(thetvdb|abstvdb)://([-a-z0-9\.]+)')

OPCODE_DATA = (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_BINARY)

responses = {
    100: ('Continue', 'Request received, please continue'),
    101: ('Switching Protocols',
          'Switching to new protocol; obey Upgrade header'),

    200: ('OK', 'Request fulfilled, document follows'),
    201: ('Created', 'Document created, URL follows'),
    202: ('Accepted',
          'Request accepted, processing continues off-line'),
    203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
    204: ('No Content', 'Request fulfilled, nothing follows'),
    205: ('Reset Content', 'Clear input form for further input.'),
    206: ('Partial Content', 'Partial content follows.'),

    300: ('Multiple Choices',
          'Object has several resources -- see URI list'),
    301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
    302: ('Found', 'Object moved temporarily -- see URI list'),
    303: ('See Other', 'Object moved -- see Method and URL list'),
    304: ('Not Modified',
          'Document has not changed since given time'),
    305: ('Use Proxy',
          'You must use proxy specified in Location to access this '
          'resource.'),
    307: ('Temporary Redirect',
          'Object moved temporarily -- see URI list'),

    400: ('Bad Request',
          'Bad request syntax or unsupported method'),
    401: ('Unauthorized',
          'Login failed'),
    402: ('Payment Required',
          'No payment -- see charging schemes'),
    403: ('Forbidden',
          'Request forbidden -- authorization will not help'),
    404: ('Not Found', 'Nothing matches the given URI'),
    405: ('Method Not Allowed',
          'Specified method is invalid for this server.'),
    406: ('Not Acceptable', 'URI not available in preferred format.'),
    407: ('Proxy Authentication Required', 'You must authenticate with '
          'this proxy before proceeding.'),
    408: ('Request Timeout', 'Request timed out; try again later.'),
    409: ('Conflict', 'Request conflict.'),
    410: ('Gone',
          'URI no longer exists and has been permanently removed.'),
    411: ('Length Required', 'Client must specify Content-Length.'),
    412: ('Precondition Failed', 'Precondition in headers is false.'),
    413: ('Request Entity Too Large', 'Entity is too large.'),
    414: ('Request-URI Too Long', 'URI is too long.'),
    415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
    416: ('Requested Range Not Satisfiable',
          'Cannot satisfy request range.'),
    417: ('Expectation Failed',
          'Expect condition could not be satisfied.'),

    500: ('Internal Server Error', 'Server got itself in trouble'),
    501: ('Not Implemented',
          'Server does not support this operation'),
    502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
    503: ('Service Unavailable',
          'The server cannot process the request due to a high load'),
    504: ('Gateway Timeout',
          'The gateway server did not receive a timely response'),
    505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
    }

####################################################################################################

def Start():
    
    global ws
    
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    
    ws = websocket.create_connection('ws://localhost:32400/:/websockets/notifications')
    
    Dict['nowPlaying'] = dict()
    
    if Prefs['start_scrobble'] and Prefs['username'] is not None:
        Log('Autostart scrobbling')
        Dict["scrobble"] = True
    else:
        Dict["scrobble"] = False
    
    #if Prefs['sync_startup'] and Prefs['username'] is not None:
    #    Log('Will autosync in 1 minute')
    #    Thread.CreateTimer(60, SyncTrakt)
    
    if Prefs['new_sync_collection'] and Prefs['username'] is not None:
        Log('Automatically sync new Items to Collection')
        Dict["new_sync_collection"] = True
    else:
        Dict["new_sync_collection"] = False
    
    Thread.Create(SocketListen)
    
####################################################################################################
def ValidatePrefs():
    
    if Prefs['username'] is None:
        return MessageContainer("Error", "No login information entered.")

    if not Prefs['sync_watched'] and not Prefs['sync_ratings'] and not Prefs['sync_collection']:
        return MessageContainer("Error", "At least one sync type need to be enabled.")

    if not Prefs['start_scrobble']:
        Dict["scrobble"] = False

    status = talk_to_trakt('account/test', {'username' : Prefs['username'], 'password' : Hash.SHA1(Prefs['password'])})

    if status['status']:
    
        if Prefs['start_scrobble']:
            Log('Autostart scrobbling')
            Dict["scrobble"] = True
        else:
            Dict['scrobble'] = False
        
        if Prefs['new_sync_collection']:
            Log('Automatically sync new Items to Collection')
            Dict["new_sync_collection"] = True
        else:
            Dict["new_sync_collection"] = False
    
        return MessageContainer(
            "Success",
            "Trakt responded with: %s " % status['message']
        )
    else:
        return MessageContainer(
            "Error",
            "Trakt responded with: %s " % status['message']
        )
####################################################################################################
@handler('/applications/trakttv', NAME, thumb=ICON, art=ART)
def MainMenu():

    oc = ObjectContainer()

    #oc.add(DirectoryObject(key=Callback(ManuallySync), title=L("Sync"), summary=L("Sync the Plex library with Trakt.tv"), thumb=R("icon-sync.png")))

    oc.add(PrefsObject(title="Preferences", summary="Configure how to connect to Trakt.tv", thumb=R("icon-preferences.png")))
    return oc
    
####################################################################################################
def SyncDownString():

    if Prefs['sync_watched'] and Prefs['sync_ratings']:
        return "seen and rated"
    elif Prefs['sync_watched']:
        return "seen "
    elif Prefs['sync_ratings']:
        return "rated "
    else:
        return ""

def SyncUpString():
    action_strings = []
    if Prefs['sync_collection']:
        action_strings.append("library")
    if Prefs['sync_watched']:
        action_strings.append("seen items")
    if Prefs['sync_ratings']:
        action_strings.append("ratings")

    temp_string = ", ".join(action_strings)
    li = temp_string.rsplit(", ", 1)
    return " and ".join(li)

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

####################################################################################################
@route('/applications/trakttv/manuallysync')
def ManuallySync():

    if Prefs['username'] is None:
        return MessageContainer("Error", "No login information entered.")

    oc = ObjectContainer(title2=L("Sync"))

    all_keys = []

    try:
        sections = XML.ElementFromURL(PMS_URL % '/library/sections', errors='ignore').xpath('//Directory')
        for section in sections:
            key = section.get('key')
            title = section.get('title')
            #Log('%s: %s' %(title, key))
            if section.get('type') == 'show' or section.get('type') == 'movie':
                oc.add(DirectoryObject(key=Callback(SyncSection, key=[key]), title='Sync items in "' + title + '" to Trakt.tv', summary='Sync your ' + SyncUpString() + ' in the "' + title + '" section of your Plex library with your Trakt.tv account.', thumb=R("icon-sync_up.png")))
                all_keys.append(key)
    except: 
        Log('Failed to load sections from PMS')
        pass

    if len(all_keys) > 1:
        oc.add(DirectoryObject(key=Callback(SyncSection, key=",".join(all_keys)), title='Sync items in ALL sections to Trakt.tv', summary='Sync your ' + SyncUpString() + ' in all sections of your Plex library with your Trakt.tv account.', thumb=R("icon-sync_up.png")))

    oc.add(DirectoryObject(key=Callback(ManuallyTrakt), title='Sync items from Trakt.tv', summary='Sync your ' + SyncDownString() + ' items on Trakt.tv with your Plex library.', thumb=R("icon-sync_down.png")))

    return oc

####################################################################################################
@route('/applications/trakttv/syncplex')
def SyncPlex():
    LAST_SYNC_UP = Dict['Last_sync_up']
    try:
        if (Dict['Last_sync_up'] + Datetime.Delta(minutes=360)) > Datetime.Now():
            Log('Not enough time since last sync, breaking!')
        else:
            all_keys = []
            try:
                sections = XML.ElementFromURL(PMS_URL % '/library/sections', errors='ignore').xpath('//Directory')
                for section in sections:
                    if section.get('type') == 'show' or section.get('type') == 'movie':
                        all_keys.append(key)
            except:
                Log("Couldn't find PMS instance")
                
            for key in all_keys:
                try:
                    SyncSection(key)
                except: pass
    except:
        all_keys = []
        try:
            sections = XML.ElementFromURL(PMS_URL % '/library/sections', errors='ignore').xpath('//Directory')
            for section in sections:
                if section.get('type') == 'show' or section.get('type') == 'movie':
                    all_keys.append(key)
        except:
            Log("Couldn't find PMS instance")
            
        for key in all_keys:
            try:
                SyncSection(key)
            except: pass

####################################################################################################
@route('/applications/trakttv/synctrakt')
def SyncTrakt():
    LAST_SYNC_DOWN = Dict['Last_sync_down']
    try:
        if (LAST_SYNC_DOWN + Datetime.Delta(minutes=360)) > Datetime.Now():
            Log('Not enough time since last sync, breaking!')
        else:
            ManuallyTrakt()
    except:
        ManuallyTrakt()

####################################################################################################
@route('/applications/trakttv/manuallytrakt')
def ManuallyTrakt():

    if Prefs['username'] is None:
        Log('You need to enter you login information first.')
        return MessageContainer('Login information missing', 'You need to enter you login information first.')

    if Prefs['sync_watched'] is not True and Prefs['sync_ratings'] is not True:
        Log('You need to enable at least one type of actions to sync first.')
        return MessageContainer('No type selected', 'You need to enable at least one type of actions to sync first.')

    values = {}
    values['username'] = Prefs['username']
    values['password'] = Hash.SHA1(Prefs['password'])
    values['extended'] = 'min'

    try:
        if Prefs['sync_watched'] is True:
            # Get data from Trakt.tv
            movie_list = talk_to_trakt('user//library/movies/watched.json', values, param = Prefs['username'])
            show_list = talk_to_trakt('user//library/shows/watched.json', values, param = Prefs['username'])
    
        if Prefs['sync_ratings'] is True:
            # Get data from Trakt.tv
            movies_rated_list = talk_to_trakt('user/ratings/movies.json', values, param = Prefs['username'])
            episodes_rated_list = talk_to_trakt('user/ratings/episodes.json', values, param = Prefs['username'])
    except:
        return MessageContainer('Failed to load data from Trakt', 'Something went wrong while getting data from Trakt. Please check the log for details.')

    #Go through the Plex library and update flags
    library_sections = XML.ElementFromURL(PMS_URL % '/library/sections', errors='ignore').xpath('//Directory')
    for library_section in library_sections:
        if library_section.get('type') == 'movie':
            videos = XML.ElementFromURL(PMS_URL % ('/library/sections/%s/all' % library_section.get('key')), errors='ignore').xpath('//Video')
            for video in videos:
                metadata = get_metadata_from_pms(video.get('ratingKey'))
                if 'imdb_id' in metadata:
                    if Prefs['sync_watched'] is True:
                        for movie in movie_list:
                            if 'imdb_id' in movie:
                                if metadata['imdb_id'] == movie['imdb_id']:
                                    Log('Found %s with id %s' % (metadata['title'], video.get('ratingKey')))
                                    # TODO: Dont mark a movie as seen if it allready is seen. Messes up the library.
                                    if video.get('viewCount') > 0:
                                        Log('The movie %s is already marked as seen in the library.' % metadata['title'] )
                                    else:
                                        request = HTTP.Request('http://localhost:32400/:/scrobble?identifier=com.plexapp.plugins.library&key=%s' % video.get('ratingKey')).content
                    if Prefs['sync_ratings'] is True:
                        for movie in movies_rated_list:
                            if 'imdb_id' in movie:
                                if metadata['imdb_id'] == movie['imdb_id']:
                                    Log('Found %s with id %s' % (metadata['title'], video.get('ratingKey')))
                                    request = HTTP.Request('http://localhost:32400/:/rate?key=%s&identifier=com.plexapp.plugins.library&rating=%s' % (video.get('ratingKey'), movie['rating_advanced'])).content
        elif library_section.get('type') == 'show':
            directories = XML.ElementFromURL(PMS_URL % ('/library/sections/%s/all' % library_section.get('key')), errors='ignore').xpath('//Directory')
            for directory in directories:
                try:
                    tvdb_id = TVSHOW1_REGEXP.search(XML.ElementFromURL(PMS_URL % ('/library/metadata/%s' % directory.get('ratingKey')), errors='ignore').xpath('//Directory')[0].get('guid')).group(2)
                    if tvdb_id != None:
                        if Prefs['sync_watched'] is True:
                            for show in show_list:
                                if tvdb_id == show['tvdb_id']:
                                    Log('We have a match for %s' % show['title'])
                                    episodes = XML.ElementFromURL(PMS_URL % ('/library/metadata/%s/allLeaves' % directory.get('ratingKey')), errors='ignore').xpath('//Video')
                                    for episode in episodes:
                                        for season in show['seasons']:
                                            if int(season['season']) == int(episode.get('parentIndex')):
                                                if int(episode.get('index')) in season['episodes']:
                                                    Log('Marking %s episode %s with key: %s as seen.' % (episode.get('grandparentTitle'), episode.get('title'), episode.get('ratingKey')))
                                                    if episode.get('viewCount') > 0:
                                                        Log('The episode %s is already marked as seen in the library.' % episode.get('title') )
                                                    else:
                                                        request = HTTP.Request('http://localhost:32400/:/scrobble?identifier=com.plexapp.plugins.library&key=%s' % episode.get('ratingKey')).content
                        if Prefs['sync_ratings'] is True:
                            for show in episodes_rated_list:
                                if int(tvdb_id) == int(show['show']['tvdb_id']):
                                    episodes = XML.ElementFromURL(PMS_URL % ('/library/metadata/%s/allLeaves' % directory.get('ratingKey')), errors='ignore').xpath('//Video')
                                    for episode in episodes:
                                        if int(show['episode']['season']) == int(episode.get('parentIndex')) and int(show['episode']['number']) == int(episode.get('index')):
                                            request = HTTP.Request('http://localhost:32400/:/rate?key=%s&identifier=com.plexapp.plugins.library&rating=%s' % (episode.get('ratingKey'), show['rating_advanced'])).content
                except: pass
    Log('Syncing is done!')
    Dict['Last_sync_down'] = Datetime.Now()
    return MessageContainer('Done', 'Syncing is done!')

####################################################################################################
@route('/applications/trakttv/syncsection')
def SyncSection(key):

    if Prefs['username'] is None:
        Log('You need to enter you login information first.')
        return MessageContainer('Login information missing', 'You need to enter you login information first.')

    if Prefs['sync_watched'] is not True and Prefs['sync_ratings'] is not True and Prefs['sync_collection'] is not True:
        Log('You need to enable at least one type of actions to sync first.')
        return MessageContainer('No type selected', 'You need to enable at least one type of actions to sync first.')

    # Sync the library with trakt.tv
    all_movies = []
    all_episodes = []
    ratings_movies = []
    ratings_episodes = []
    collection_movies = []
    collection_episodes = []
    Log(key)


    for value in key.split(','):
        item_kind = XML.ElementFromURL(PMS_URL % ('/library/sections/%s/all' % value), errors='ignore').xpath('//MediaContainer')[0].get('viewGroup')
        if item_kind == 'movie':
            videos = XML.ElementFromURL(PMS_URL % ('/library/sections/%s/all' % value), errors='ignore').xpath('//Video')
            for video in videos:
                pms_metadata = None
                if Prefs['sync_collection'] is True:
                    pms_metadata = get_metadata_from_pms(video.get('ratingKey'))
                    collection_movie = pms_metadata
                    collection_movies.append(collection_movie)
                    
                if video.get('viewCount') > 0:
                    Log('You have seen %s', video.get('title'))
                    if video.get('type') == 'movie':
                        if pms_metadata is None:
                            pms_metadata = get_metadata_from_pms(video.get('ratingKey'))
                        movie_dict = pms_metadata
                        movie_dict['plays'] = int(video.get('viewCount'))
                        # Remove the duration value since we won't need that!
                        #movie_dict.pop('duration')
                        all_movies.append(movie_dict)
                    else:
                        Log('Unknown item %s' % video.get('ratingKey'))
                if video.get('userRating') != None:
                    if pms_metadata is None:
                        pms_metadata = get_metadata_from_pms(video.get('ratingKey'))
                    rating_movie = pms_metadata
                    rating_movie['rating'] = int(video.get('userRating'))
                    ratings_movies.append(rating_movie)
        elif item_kind == 'show':
            directories = XML.ElementFromURL(PMS_URL % ('/library/sections/%s/all' % value), errors='ignore').xpath('//Directory')
            for directory in directories:
                try:
                    tvdb_id = TVSHOW1_REGEXP.search(XML.ElementFromURL(PMS_URL % ('/library/metadata/%s' % directory.get('ratingKey')), errors='ignore').xpath('//Directory')[0].get('guid')).group(2)
                except:
                    tvdb_id = None
    
                tv_show = {}
                tv_show['title'] = directory.get('title')
                if directory.get('year') is not None:
                    tv_show['year'] = int(directory.get('year'))
                if tvdb_id is not None:
                    tv_show['tvdb_id'] = tvdb_id
    
                seen_episodes = []
                collected_episodes = []
                episodes = XML.ElementFromURL(PMS_URL % ('/library/metadata/%s/allLeaves' % directory.get('ratingKey')), errors='ignore').xpath('//Video')
                for episode in episodes:
                    try:
                        collected_episode = {}
                        collected_episode['season'] = int(episode.get('parentIndex'))
                        collected_episode['episode'] = int(episode.get('index'))
                        collected_episodes.append(collected_episode)
                    except: pass
                    if episode.get('viewCount') > 0:
                        try:
                            tv_episode = {}
                            tv_episode['season'] = int(episode.get('parentIndex'))
                            tv_episode['episode'] = int(episode.get('index'))
                            seen_episodes.append(tv_episode)
                        except: pass
                    if episode.get('userRating') != None:
                        try:
                            rating_episode = {}
                            rating_episode['season'] = int(episode.get('parentIndex'))
                            rating_episode['episode'] = int(episode.get('index'))
                            rating_episode['rating'] = int(episode.get('userRating'))
                            rating_episode['title'] = directory.get('title')
                            if directory.get('year') is not None:
                                rating_episode['year'] = int(directory.get('year'))
                            if tvdb_id is not None:
                                rating_episode['tvdb_id'] = tvdb_id
                            ratings_episodes.append(rating_episode)
                        except: pass
                if len(seen_episodes) > 0:
                    seen_tv_show = {}
                    seen_tv_show['title'] = directory.get('title')
                    if directory.get('year') is not None:
                        seen_tv_show['year'] = int(directory.get('year'))
                    if tvdb_id is not None:
                        seen_tv_show['tvdb_id'] = tvdb_id
                    seen_tv_show['episodes'] = seen_episodes
                    all_episodes.append(seen_tv_show)
                tv_show['episodes'] = collected_episodes
                collection_episodes.append(tv_show)
                        

    Log('Found %s movies' % len(all_movies))
    Log('Found %s series' % len(all_episodes))
    
    if Prefs['sync_ratings'] is True:
        if len(ratings_episodes) > 0:
            values = {}
            values['username'] = Prefs['username']
            values['password'] = Hash.SHA1(Prefs['password'])
            values['episodes'] = ratings_episodes
            status = talk_to_trakt('rate/episodes', values)
            Log("Trakt responded with: %s " % status)
    
        if len(ratings_movies) > 0:
            values = {}
            values['username'] = Prefs['username']
            values['password'] = Hash.SHA1(Prefs['password'])
            values['movies'] = ratings_movies
            status = talk_to_trakt('rate/movies', values)
            Log("Trakt responded with: %s " % status)

    if Prefs['sync_watched'] is True:
        if len(all_movies) > 0:
            values = {}
            values['username'] = Prefs['username']
            values['password'] = Hash.SHA1(Prefs['password'])
            values['movies'] = all_movies
            status = talk_to_trakt('movie/seen', values)
            Log("Trakt responded with: %s " % status)
        for episode in all_episodes:
            episode['username'] = Prefs['username']
            episode['password'] = Hash.SHA1(Prefs['password'])
            status = talk_to_trakt('show/episode/seen', episode)
            Log("Trakt responded with: %s " % status)

    if Prefs['sync_collection'] is True:
        if len(collection_movies) > 0:
            values = {}
            values['username'] = Prefs['username']
            values['password'] = Hash.SHA1(Prefs['password'])
            values['movies'] = collection_movies
            status = talk_to_trakt('movie/library', values)
            Log("Trakt responded with: %s " % status)
        for episode in collection_episodes:
            episode['username'] = Prefs['username']
            episode['password'] = Hash.SHA1(Prefs['password'])
            status = talk_to_trakt('show/episode/library', episode)
            Log("Trakt responded with: %s " % status)

    Log('Syncing is done!')
    Dict['Last_sync_up'] = Datetime.Now()
    return MessageContainer('Done', 'Syncing is done!')

####################################################################################################
@route('/applications/trakttv/talk_to_trakt')
def talk_to_trakt(action, values, param = ""):

    if param != "":
        param = "/" + param
    # Function to talk to the trakt.tv api
    data_url = TRAKT_URL % (action, param)
    
    values['username'] = Prefs['username']
    values['password'] =  Hash.SHA1(Prefs['password'])
    values['plugin_version'] =  PLUGIN_VERSION
    # TODO
    values['media_center_version'] =  '%s, %s' % (Platform.OS, Platform.CPU)
    
    try:
        json_file = HTTP.Request(data_url, data=JSON.StringFromObject(values))
        headers = json_file.headers
        result = JSON.ObjectFromString(json_file.content)
        #Log(result)

    except Ex.HTTPError, e:
        result = {'status' : 'failure', 'error' : responses[e.code][1]}
    except Ex.URLError, e:
        return {'status' : 'failure', 'error' : e.reason[0]}

    try:
        if result['status'] == 'success':
            if not 'message' in result:
                result['message'] = 'Unknown success'
            Log('Trakt responded with: %s' % result['message'])
            return {'status' : True, 'message' : result['message']}
        elif result['status'] == 'failure':
            Log('Trakt responded with: %s' % result['error'])
            return {'status' : False, 'message' : result['error']}
    except:
        Log('Return all')
        return result

####################################################################################################
@route('/applications/trakttv/get_metadata_from_pms')
def get_metadata_from_pms(item_id):
    # Prepare a dict that contains all the metadata required for trakt.
    pms_url = PMS_URL % ('/library/metadata/' + str(item_id))

    try:
        xml_file = HTTP.Request(pms_url)
        xml_content = XML.ElementFromString(xml_file).xpath('//Video')
        for section in xml_content:
            metadata = dict()
            
            try:
                metadata['duration'] = int(float(section.get('duration'))/60000)
            except: pass

            if section.get('year') is not None:
                metadata['year'] = int(section.get('year'))
            
            metadata['type'] = section.get('type')
            
            if metadata['type'] == 'movie':
                metadata['title'] = section.get('title')
                
                try:
                    metadata['imdb_id'] = MOVIE_REGEXP.search(section.get('guid')).group(1)
                except:
                    metadata['imdb_id'] = False
                    try:
                        metadata['tmdb_id'] = MOVIEDB_REGEXP.search(section.get('guid')).group(1)
                    except:
                        try:
                            metadata['tmdb_id'] = STANDALONE_REGEXP.search(section.get('guid')).group(1)
                        except:
                            Log('The movie %s doesn\'t have any imdb or tmdb id, it will be ignored.' % section.get('title'))
                            metadata['tmdb_id'] = False
            
            elif metadata['type'] == 'episode':
                metadata['title'] = section.get('grandparentTitle')
                metadata['episode_title'] = section.get('title')
                
                try:
                    m = TVSHOW_REGEXP.search(section.get('guid'))
                    metadata['tvdb_id'] = m.group(2)
                    metadata['season'] = m.group(3)
                    metadata['episode'] = m.group(4)
                except:
                    Log('The episode %s doesn\'t have any tvdb id, it will not be ignored.' % section.get('title'))
                    metadata['tvdb_id'] = False
            else:
                Log('The content type %s is not supported, the item %s will not be ignored.' % (section.get('type'), section.get('title')))

            return metadata
    except Ex.HTTPError, e:
        Log('Failed to connect to %s.' % pms_url)
        return {'status' : False, 'message' : responses[e.code][1]}
    except Ex.URLError, e:
        Log('Failed to connect to %s.' % pms_url)
        return {'status' : False, 'message' : e.reason[0]}

####################################################################################################
@route('/applications/trakttv/socketlisten')
def SocketListen():
    
    def SocketRecv():
        frame = ws.recv_frame()
        if not frame:
            raise websocket.WebSocketException("Not a valid frame %s" % frame)
        elif frame.opcode in OPCODE_DATA:
            return (frame.opcode, frame.data)
        elif frame.opcode == websocket.ABNF.OPCODE_CLOSE:
            ws.send_close()
            return (frame.opcode, None)
        elif frame.opcode == websocket.ABNF.OPCODE_PING:
            ws.pong("Hi!")
    
        return None, None
    
    while True:
        opcode, data = SocketRecv()
        msg = None
        if opcode in OPCODE_DATA:
            info = JSON.ObjectFromString(data)
            
            #scrobble
            if info['type'] == "playing" and Dict["scrobble"]:
                sessionKey = str(info['_children'][0]['sessionKey'])
                state = str(info['_children'][0]['state'])
                viewOffset = str(info['_children'][0]['viewOffset'])
                Log.Info(sessionKey + " - " + state + ' - ' + viewOffset)
                Scrobble(sessionKey,state,viewOffset)
            
            #adding to collection
            elif info['type'] == "timeline" and Dict['new_sync_collection']:
                if (info['_children'][0]['type'] == 1 or info['_children'][0]['type'] == 4) and info['_children'][0]['state'] == 0:
                    Log.Info("New File added to Libray: " + info['_children'][0]['title'] + ' - ' + str(info['_children'][0]['itemID']))
                    itemID = info['_children'][0]['itemID']
                    # delay sync to wait for metadata
                    Thread.CreateTimer(60, CollectionSync,True,itemID,'add')
                
                # #deleted file (doesn't work yet)
                # elif (info['_children'][0]['type'] == 1 or info['_children'][0]['type'] == 4) and info['_children'][0]['state'] == 9:
                #     Log.Info("File deleted from Libray: " + info['_children'][0]['title'] + ' - ' + str(info['_children'][0]['itemID']))
                #     itemID = info['_children'][0]['itemID']
                #     # delay sync to wait for metadata
                #     #Thread.CreateTimer(10, CollectionSync,True,itemID,'add')
                #     CollectionSync(itemID,'delete')
    return

####################################################################################################
@route('/applications/trakttv/scrobble')
def Scrobble(sessionKey,state,viewOffset):
 
    if not Dict["scrobble"]: return
    else: pass
    
    if not sessionKey in Dict['nowPlaying']:
        Log.Info('getting MetaData for current media')

        try:
            pms_url = PMS_URL % ('/status/sessions/')
            xml_content = XML.ElementFromURL(pms_url).xpath('//MediaContainer/Video')
            for section in xml_content:
                if section.get('sessionKey') == sessionKey:
                    Dict['nowPlaying'][sessionKey] = get_metadata_from_pms(section.get('ratingKey'))
                    
                    Dict['nowPlaying'][sessionKey]['UserName'] = ''
                    Dict['nowPlaying'][sessionKey]['UserID'] = ''
                    
                    for user in section.findall('User'):
                        Dict['nowPlaying'][sessionKey]['UserName'] = user.get('title')
                        Dict['nowPlaying'][sessionKey]['UserID'] = user.get('id')
                    
                    # setup some variables in Dict
                    Dict['nowPlaying'][sessionKey]['Last_updated'] = Datetime.FromTimestamp(0)
                    Dict['nowPlaying'][sessionKey]['scrobbled'] = False
                    Dict['nowPlaying'][sessionKey]['cur_state'] = state
            
            # if session wasn't found, return False
            if not (sessionKey in Dict['nowPlaying']):
                Log.Info('Session data not found')
                return
                
        except Ex.HTTPError, e:
            Log.Error('Failed to connect to %s.' % pms_url)
            return
        except Ex.URLError, e:
            Log.Error('Failed to connect to %s.' % pms_url)
            return
    
    # Is it played by the correct user? Else return false
    if (Prefs['scrobble_names'] != "") and (Prefs['scrobble_names'] != Dict['nowPlaying'][sessionKey]['UserName']):
        Log.Info('Ignoring item played by other user')
        return
    
    # Is it a movie or a serie? Else return false
    if Dict['nowPlaying'][sessionKey]['type'] == 'episode' and Dict['nowPlaying'][sessionKey]['tvdb_id'] != False:
        action = 'show/'
    elif Dict['nowPlaying'][sessionKey]['type'] == 'movie' and (Dict['nowPlaying'][sessionKey]['imdb_id'] != False or Dict['nowPlaying'][sessionKey]['tmdb_id'] != False):
        action = 'movie/'
    else:
        # Not a movie or TV-Show or have incorrect metadata!
        Log('Playing unknown item, will not be scrobbled!')
        return
    
    # calculate play progress
    Dict['nowPlaying'][sessionKey]['progress'] = int(round((float(viewOffset)/(Dict['nowPlaying'][sessionKey]['duration']*60*1000))*100, 0))
    
    if (Dict['nowPlaying'][sessionKey]['scrobbled'] != True):
        # state changed, force update
        if (state != Dict['nowPlaying'][sessionKey]['cur_state']):
            if (state == 'stopped') or (state == 'paused'):
                Log.Info('Media paused or stopped, cancel watching')
                action += 'cancelwatching'
            elif (state == 'playing'):
                Log.Info('Updating watch status')
                action += 'watching'
        
        # update every 10 min
        elif state == 'playing' and ((Dict['nowPlaying'][sessionKey]['Last_updated'] + Datetime.Delta(minutes=10)) < Datetime.Now()) and Dict['nowPlaying'][sessionKey]['progress'] < 80:
            Log.Info('Updating watch status')
            action += 'watching'
        
        #scrobble item
        elif state == 'playing' and Dict['nowPlaying'][sessionKey]['progress'] > 80:
            Log.Info('Scrobble Item')
            action += 'scrobble'
            Dict['nowPlaying'][sessionKey]['scrobbled'] = True
        else:
            # Already watching or already scrobbled
            Log.Info('Nothing to do this time, all that could be done is done!')
            return
    else:
        # Already watching or already scrobbled
        Log.Info('Nothing to do this time, all that could be done is done!')
        return
    
    # Setup Data to send to Trakt
    values = dict()
    
    if Dict['nowPlaying'][sessionKey]['type'] == 'episode':
        values['tvdb_id'] = Dict['nowPlaying'][sessionKey]['tvdb_id']
        values['season'] = Dict['nowPlaying'][sessionKey]['season']
        values['episode'] = Dict['nowPlaying'][sessionKey]['episode']
    elif Dict['nowPlaying'][sessionKey]['type'] == 'movie':
        if (Dict['nowPlaying'][sessionKey]['imdb_id'] != False):
            values['imdb_id'] = Dict['nowPlaying'][sessionKey]['imdb_id']
        elif (Dict['nowPlaying'][sessionKey]['tmdb_id'] != False):
            values['tmdb_id'] = Dict['nowPlaying'][sessionKey]['tmdb_id']
    
    values['duration'] = Dict['nowPlaying'][sessionKey]['duration']
    values['progress'] = Dict['nowPlaying'][sessionKey]['progress']
    
    values['title'] = Dict['nowPlaying'][sessionKey]['title']
    if ('year' in Dict['nowPlaying'][sessionKey]):
        values['year'] = Dict['nowPlaying'][sessionKey]['year']
    
    result = talk_to_trakt(action, values)
    # Only update the action if trakt responds with a success.
    if result['status']:
        if (state == 'stopped' or state == 'paused'):
            del Dict['nowPlaying'][sessionKey] #delete session from Dict
        else:
            Dict['nowPlaying'][sessionKey]['cur_state'] = state
            Dict['nowPlaying'][sessionKey]['Last_updated'] = Datetime.Now()

    return 

####################################################################################################
@route('/applications/trakttv/collectionsync')
def CollectionSync(itemID,do):
    metadata = get_metadata_from_pms(itemID)
    Log(metadata)
    
    #cancel, if metadata is not there yet
    if not 'tvdb_id' in metadata and not 'imdb_id' in metadata and not 'tmdb_id' in metadata:
        return
    
    if do == 'add':
        do_action = 'library'
    elif do == 'delete':
        do_action = 'unlibrary'
    
    if metadata['type'] == 'episode':
        action = 'show/episode/%s' % do_action
    elif metadata['type'] == 'movie':
        action = 'movie/%s' % do_action
    
    # Setup Data to send to Trakt
    values = dict()
    
    if metadata['type'] == 'episode':
        if metadata['tvdb_id'] == False:
            Log('Added episode has no tvdb_id')
            return
        
        values['tvdb_id'] = metadata['tvdb_id']
        values['episodes'] = [{'season' : metadata['season'],'episode' : metadata['episode']}]
    elif metadata['type'] == 'movie':
        if metadata['imdb_id'] == False and 'tmdb_id' in metadata and metadata['tmdb_id'] == False:
            Log('Added movie has no imdb_id and no tmdb_id')
            return
            
        if (metadata['imdb_id'] != False):
            values['imdb_id'] = metadata['imdb_id']
        elif (metadata['tmdb_id'] != False):
            values['tmdb_id'] = metadata['tmdb_id']
        
    values['title'] = metadata['title']
    if ('year' in metadata):
        values['year'] = metadata['year']
    
    Log(values)
    
    result = talk_to_trakt(action, values)
    Log(result)
    # if result['status']:    
        
    
    return
