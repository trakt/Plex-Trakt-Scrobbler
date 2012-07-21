import fileinput
import time
from LogSucker import ReadLog

APPLICATIONS_PREFIX = "/applications/trakttv"

NAME = L('Title')

# make sure to replace artwork with what you want
# these filenames reference the example files in
# the Contents/Resources/ folder in the bundle
ART  = 'art-default.jpg'
ICON = 'icon-default.png'
PREF_ICON = 'icon-preferences.png'
PMS_URL = 'http://localhost:32400/library/%s'
TRAKT_URL = 'http://api.trakt.tv/%s/ba5aa61249c02dc5406232da20f6e768f3c82b28'

#Regexps to load data from strings
LOG_REGEXP = Regex('(?P<key>\w*?)=(?P<value>\w+\w?)')
MOVIE_REGEXP = Regex('com.plexapp.agents.imdb://(tt[-a-z0-9\.]+)')
TVSHOW_REGEXP = Regex('com.plexapp.agents.thetvdb://([-a-z0-9\.]+)/([-a-z0-9\.]+)/([-a-z0-9\.]+)')
TVSHOW1_REGEXP = Regex('com.plexapp.agents.thetvdb://([-a-z0-9\.]+)')

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

    ## make this plugin show up in the 'Applications' section
    ## in Plex. The L() function pulls the string out of the strings
    ## file in the Contents/Strings/ folder in the bundle
    ## see also:
    ##  http://dev.plexapp.com/docs/mod_Plugin.html
    ##  http://dev.plexapp.com/docs/Bundle.html#the-strings-directory
    Plugin.AddPrefixHandler(APPLICATIONS_PREFIX, ApplicationsMainMenu, NAME, ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    ## set some defaults so that you don't have to
    ## pass these parameters to these object types
    ## every single time
    ## see also:
    ##  http://dev.plexapp.com/docs/Objects.html
    MediaContainer.title1 = NAME
    MediaContainer.viewGroup = "List"
    MediaContainer.art = R(ART)
    DirectoryItem.thumb = R(ICON)
    VideoItem.thumb = R(ICON)
    
    if Prefs['start_scrobble'] and Prefs['username'] is not None:
        Log('Autostart scrobbling')
        Dict["scrobble"] = True
        Thread.Create(Scrobble)
    

def ValidatePrefs():
    u = Prefs['username']
    p = Prefs['password']
    ## do some checks and return a
    ## message container
    
    if Prefs['username'] is None:
        return MessageContainer("Error", "No login information entered.")

    status = talk_to_trakt('account/test', {'username' : u, 'password' : Hash.SHA1(p)})
    if status['status']:
        return MessageContainer(
            "Success",
            "Trakt responded with: %s " % status['message']
        )
    else:
        return MessageContainer(
            "Error",
            "Trakt responded with: %s " % status['message']
        )

def ApplicationsMainMenu():

    dir = MediaContainer(viewGroup="InfoList", noCache=True)
    
    if Dict["scrobble"]: 
        toggle_string = "Scrobbling is currently enabled, click here to disable it."
    else:
        toggle_string = "Scrobbling is currently disabled, click here to enable it."
    
    dir.Append(
        Function(
            DirectoryItem(
                ToggleScrobbling,
                "Toggle Scrobbling",
                summary=toggle_string,
                thumb=R(ICON),
                art=R(ART)
            )
        )
    )

    dir.Append(
        Function(
            DirectoryItem(
                ManuallySync,
                title="Sync the Plex library with Trakt.tv",
                subtile="Sync the Plex library with Trakt.tv",
                summary="Sync the Plex library with Trakt.tv",
                thumb=R(ICON)
            )
        )
    )

    dir.Append(
        PrefsItem(
            title="Preferences",
            subtile="Configure your Trakt.tv account",
            summary="Configure how to connect to Trakt.tv",
            thumb=R(PREF_ICON)
        )
    )


    # ... and then return the container
    return dir

def ManuallySync(sender):

    if Prefs['username'] is None:
        return MessageContainer("Error", "No login information entered.")

    dir = MediaContainer(noCache=True)

    all_keys = []

    try:
        sections = XML.ElementFromURL(PMS_URL % 'sections', errors='ignore').xpath('//Directory')
        for section in sections:
            key = section.get('key')
            title = section.get('title')
            Log('%s: %s' %(title, key))
            if section.get('type') == 'show' or section.get('type') == 'movie':
                dir.Append(Function(DirectoryItem(SyncSection, title='Sync "' + title + '" to Trakt.tv', summary='Sync the "' + title + '" section from your Plex library with Trakt.tv'), title=title, key=[key]))
                all_keys.append(key)
    except:
        dir.header = "Couldn't find PMS instance"
        dir.message = "Add or update the address of PMS in the plugin's preferences"

    if len(all_keys) > 1:
        dir.Append(Function(DirectoryItem(SyncSection, title='Sync all sections to Trakt.tv', summary='Sync all sections in Plex library with Trakt.tv'), title='Sync all sections to Trakt.tv', key=all_keys))
        dir.Append(Function(DirectoryItem(SyncTrakt, title='Sync Trakt.tv with Plex', summary='Sync your seen items on Trakt.tv with your Plex library'), title='Sync Trakt.tv with Plex'))

    return dir

def SyncTrakt(sender, title):

    if Prefs['username'] is None:
        return MessageContainer('Login information missing', 'You need to enter you login information first.')

    return MessageContainer('Not implemented', 'Not implemented.')

def SyncSection(sender, title, key):

    if Prefs['username'] is None:
        return MessageContainer('Login information missing', 'You need to enter you login information first.')

    # Sync the library with trakt.tv
    all_movies = []
    all_episodes = []

    for value in key:
        # TODO: is the section containing movies or tvshows?
        item_kind = XML.ElementFromURL(PMS_URL % ('sections/%s/all' % value), errors='ignore').xpath('//MediaContainer')[0].get('viewGroup')
        if item_kind == 'movie':
            videos = XML.ElementFromURL(PMS_URL % ('sections/%s/all' % value), errors='ignore').xpath('//Video')
            for video in videos:
                if video.get('viewCount') > 0:
                    Log('You have seen %s', video.get('title'))
                    if video.get('type') == 'movie':
                        movie_dict = get_metadata_from_pms(video.get('ratingKey'))
                        movie_dict['plays'] = int(video.get('viewCount'))
                        movie_dict['last_played'] = int(video.get('updatedAt'))
                        # Remove the duration value since we won't need that!
                        movie_dict.pop('duration')
                        all_movies.append(movie_dict)
                    else:
                        Log('Unknown item %s' % video.get('ratingKey'))
        elif item_kind == 'show':
            directories = XML.ElementFromURL(PMS_URL % ('sections/%s/all' % value), errors='ignore').xpath('//Directory')
            for directory in directories:
                # If user has seen all shows mark as seen by show
                try:
                    tvdb_id = TVSHOW1_REGEXP.search(XML.ElementFromURL(PMS_URL % ('metadata/%s' % directory.get('ratingKey')), errors='ignore').xpath('//Directory')[0].get('guid')).group(1)
                except:
                    tvdb_id = None

                tv_show = {}
                tv_show['title'] = directory.get('title')
                if directory.get('year') is not None:
                    tv_show['year'] = directory.get('year')
                if tvdb_id is not None:
                    tv_show['tvdb_id'] = tvdb_id

                seen_episodes = []
                episodes = XML.ElementFromURL(PMS_URL % ('metadata/%s/allLeaves' % directory.get('ratingKey')), errors='ignore').xpath('//Video')
                for episode in episodes:
                    if episode.get('viewCount') > 0:
                        tv_episode = {}
                        tv_episode['season'] = int(episode.get('parentIndex'))
                        tv_episode['episode'] = int(episode.get('index'))
                        seen_episodes.append(tv_episode)
                tv_show['episodes'] = seen_episodes
                all_episodes.append(tv_show)
                        

    Log('Found %s movies' % len(all_movies))
    Log('Found %s series' % len(all_episodes))

    if len(all_movies) > 0:
        values = {}
        values['username'] = Prefs['username']
        values['password'] = Hash.SHA1(Prefs['password'])
        values['movies'] = all_movies
        status = talk_to_trakt('movie/seen', values)
        #Log("Trakt responded with: %s " % status)
    for episode in all_episodes:
        if len(episode['episodes']) > 0:
            values = {}
            episode['username'] = Prefs['username']
            episode['password'] = Hash.SHA1(Prefs['password'])
            status = talk_to_trakt('show/episode/seen', episode)
    #        Log("Trakt responded with: %s " % status['message'])

    return MessageContainer(title, 'Done')

def watch_or_scrobble(item_id, progress):
    # Function to add what currently is playing to trakt, decide o watch or scrobble
    LAST_USED_ID = Dict['Last_used_id']
    LAST_USED_ACTION = Dict['Last_used_action']
    values = Dict['Last_used_metadata']
    LAST_UPDATED = Dict['Last_updated']
    Log('Current id: %s and previous id: %s using action: %s' % (item_id, LAST_USED_ID, LAST_USED_ACTION))

    if item_id != LAST_USED_ID:
        # Reset all parameters since the user has changes what they are watching.
        Log('Lets refresh the metadata')
        values = get_metadata_from_pms(item_id)
        Dict['Last_used_metadata'] = values
        Dict['Last_used_id'] = item_id
        LAST_USED_ACTION = None
        LAST_UPDATED = None

    progress = int(float(progress)/60000)
    values['progress'] = round((float(progress)/values['duration'])*100, 0)
    
    # Just for debugging
    Log(values)
    
    # Add username and password to values
    values['username'] = Prefs['username']
    values['password'] =  Hash.SHA1(Prefs['password'])

    # Is it a movie or a serie? Else return false
    if 'tvdb_id' in values:
        action = 'show/'
        #Log('This is a tv show')
    elif 'imdb_id' in values:
        action = 'movie/'
        #Log('This is a movie')
    else:
        # Not a movie or TV-Show or have incorrect metadata!
        Log('Unknown item, bail out!')
        return false

    if item_id != LAST_USED_ID:
        action += 'watching'
        Dict['Last_used_action'] = 'watching'
        Dict['Last_updated'] = Datetime.Now()
    elif LAST_USED_ACTION == 'watching' and (LAST_UPDATED + Datetime.Delta(minutes=10)) < Datetime.Now() and values['progress'] < 85.0:
        Log('More than 10 minutes since last update')
        action += 'watching'
        Dict['Last_used_action'] = 'watching'
        Dict['Last_updated'] = Datetime.Now()
    elif LAST_USED_ACTION == 'watching' and values['progress'] > 85.0:
        action += 'scrobble'
        Dict['Last_used_action'] = 'scrobble'
    else:
        # Already watching or already scrobbled
        Log('Nothing to do this time, all that could be done is done!')
        return false
    
    result = talk_to_trakt(action, values)
    Log(result)

    return result

def talk_to_trakt(action, values):
    # Function to talk to the trakt.tv api
    data_url = TRAKT_URL % action
    
    Log(values)
    
    try:
        json_file = HTTP.Request(data_url, data=JSON.StringFromObject(values))
        headers = json_file.headers
        result = JSON.ObjectFromString(json_file.content)
        Log(result)

    except Ex.HTTPError, e:
        result = {'status' : 'failure', 'error' : responses[e.code][1]}
    except Ex.URLError, e:
        return {'status' : 'failure', 'error' : e.reason[0]}

    if result['status'] == 'success':
        if not 'message' in result:
           result['message'] = 'Unknown'
        Log('Trakt responded with: %s' % result['message'])
        return {'status' : True, 'message' : result['message']}
    else:
        Log('Trakt responded with: %s' % result['error'])
        return {'status' : False, 'message' : result['error']}

def get_metadata_from_pms(item_id):
    # Prepare a dict that contains all the metadata required for trakt.
    pms_url = PMS_URL % ('metadata/' + str(item_id))
    Log(pms_url)
    try:
        xml_file = HTTP.Request(pms_url)
        xml_content = XML.ElementFromString(xml_file).xpath('//Video')
        for section in xml_content:
            #Log(section)
            metadata = {'title' : section.get('title'), 'duration' : int(float(section.get('duration'))/60000)}
            if section.get('year') is not None:
                metadata['year'] = int(section.get('year'))

            if section.get('type') == 'movie':
                try:
                    metadata['imdb_id'] = MOVIE_REGEXP.search(section.get('guid')).group(1)
                except:
                    Log('The movie %s doesn\'t have any imdb id, it will not be scrobbled.' % section.get('title'))
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
        return {'status' : False, 'message' : responses[e.code][1]}
    except Ex.URLError, e:
        Log('Failed to connect to %s.' % pms_url)
        return {'status' : False, 'message' : e.reason[0]}

def LogPath():
    return Core.storage.abs_path(Core.storage.join_path(Core.log.handlers[1].baseFilename, '..', '..', 'Plex Media Server.log'))

def ToggleScrobbling(sender):
    if not Dict["scrobble"]:
        if Prefs['username'] is None:
            return MessageContainer('Login information missing', 'You need to enter you login information first.')
        Dict["scrobble"] = True
        Log("Start scrobbling")
        Thread.Create(Scrobble)
        return MessageContainer(NAME, L('Now scrobbling what you watch.'))
    else:
        Dict["scrobble"] = False
        return MessageContainer(NAME, L('Scrobbling is now stopped.'))

def Scrobble():
    log_path = LogPath()
    Log("LogPath='%s'" % log_path)
    log_data = ReadLog(log_path, True)
    line = log_data['line']
    
    while 1:
        if not Dict["scrobble"]: break
        else: pass

        #Grab the next line of the log#
        log_data = ReadLog(log_path, False, log_data['where'])
        line = log_data['line']
        try:
            log_values = dict(LOG_REGEXP.findall(line))
            #Log(log_values)
            if log_values['key'] != None:
                #Log('Playing something')
                watch_or_scrobble(log_values['key'], log_values['time'])
        except:
            pass

    return 
