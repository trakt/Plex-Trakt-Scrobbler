import logsucker
#import hashlib
import re
import fileinput

APPLICATIONS_PREFIX = "/applications/trakttv"

NAME = L('Title')

# make sure to replace artwork with what you want
# these filenames reference the example files in
# the Contents/Resources/ folder in the bundle
ART  = 'art-default.jpg'
ICON = 'icon-default.png'
PMS_URL = 'http://%s/library/%s'
TRAKT_URL = 'http://api.trakt.tv/%s/ba5aa61249c02dc5406232da20f6e768f3c82b28'

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
    Log(Platform.OS)


def ValidatePrefs():
    u = Prefs['username']
    p = Prefs['password']
    ## do some checks and return a
    ## message container
    

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
    dir.Append(
        Function(
            DirectoryItem(
                ManuallySync,
                "Manually Sync to trakt.tv",
                summary="Sync current library to trakt.tv",
                thumb=R(ICON),
                art=R(ART)
            )
        )
    )
    if not Dict["scrobble"]: ### THIS TEST DOESN'T CURRENTLY WORK IN THE DESKTOP CLIENT BECAUSE OF A CACHE BUG. IT SHOULD BE FIXED FOR US (HOPEFULLY SOON) ###
        dir.Append(
            Function(
                DirectoryItem(
                    StartScrobbling,
                    "Start Scrobbling",
                    thumb=R(ICON),
                    art=R(ART)
                )
            )   
        )
    else:
        dir.Append(
            Function(
                DirectoryItem(
                    StopScrobbling,
                    "Stop Scrobbling",
                    thumb=R(ICON),
                    art=R(ART)
                )
            )   
        )
    dir.Append(
        PrefsItem(
            title="Trakt.tv preferences",
            subtile="Configure your trakt.tv account",
            summary="Configure how to connect to trakt.tv",
            thumb=R(ICON)
        )
    )
    

    # ... and then return the container
    return dir

def ManuallySync(sender):

    status = watch_or_scrobble(132, 300000)
    if status['status']:
        return MessageContainer('Works', 'Trakt.tv said %s.' % status['message'])
    else:
        return MessageContainer('Failed', 'Trakt.tv said %s.' % status['message'])

def watch_or_scrobble(item_id, progress):
    # Function to add what currently is playing to trakt, decide o watch or scrobble
    values = get_metadata_from_pms(item_id)
    progress = int(float(progress)/60000)
    values['progress'] = round((float(progress)/values['duration'])*100, 0)
    # Add username and pssword to values
    values['username'] = Prefs['username']
    values['password'] =  Hash.SHA1(Prefs['password'])

    # Just for debugging
    Log(values)
    
    if 'tvdb_id' in values:
        action = 'show/'
    elif 'imdb_id' in values:
        action = 'movie/'
    else:
        # Todo
        Log('Figure out how to bail out.')
    
    if values['progress'] > 85.0:
        Log('We will scrobble it')
        action += 'scrobble'
    else:
        Log('We will watch it')
        action += 'watching'
    
    result = talk_to_trakt(action, values)
    Log(result)
    return result

def talk_to_trakt(action, values):
    # Function to talk to the trakt.tv api
    data_url = TRAKT_URL % action
    
    try:
        json_file = HTTP.Request(data_url, values=values)
        headers = json_file.headers
        result = JSON.ObjectFromString(json_file.content)
        Log(result)

    except Ex.HTTPError, e:
        result = {'status' : 'failure', 'error' : responses[e.code][1]}
    except Ex.URLError, e:
        return {'status' : 'failure', 'error' : e.reason[0]}

    if result['status'] == 'success':
        Log('Trakt responded with: %s' % result['message'])
        return {'status' : True, 'message' : result['message']}
    else:
        Log('Trakt responded with: %s' % result['error'])
        return {'status' : False, 'message' : result['error']}

def get_metadata_from_pms(item_id):
    # Prepare a dict that contains all the metadata required for trakt.
    host = Prefs['pms_host']

    if host.find(':') == -1:
        host += ':32400'

    pms_url = PMS_URL % (host, 'metadata/' + str(item_id))
    Log(pms_url)
    try:
        xml_file = HTTP.Request(pms_url)
        xml_content = XML.ElementFromString(xml_file).xpath('//Video')
        for section in xml_content:
            #Log(section)
            metadata = {'title' : section.get('title'), 'year' : section.get('year'), 'duration' : int(float(section.get('duration'))/60000)}

            if section.get('type') == 'movie':
                try:
                    m = re.search('com.plexapp.agents.imdb://(tt[-a-z0-9\.]+)', section.get('guid'))
                    metadata['imdb_id'] = m.group(1)
                    metadata['status'] = True
                except:
                    Log('The movie %s doesn\'t have any imdb id, it will not be scrobbled.' % section.get('title'))
            elif section.get('type') == 'episode':
                try:
                    m = re.search('com.plexapp.agents.thetvdb://([-a-z0-9\.]+)/([-a-z0-9\.]+)/([-a-z0-9\.]+)', section.get('guid'))
                    metadata['tvdb_id'] = m.group(1)
                    metadata['season'] = m.group(2)
                    metadata['episode'] = m.group(3)
                    metadata['status'] = True
                except:
                    metadata['status'] = False
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

def StartScrobbling(sender):
    Dict["scrobble"] = True
    Log("Start scrobbling")
    LogSucker = Thread.Create(ReadLog())
    return MessageContainer(NAME, L('Now scrobbling what you watch.'))
    
def StopScrobbling(sender):
    Dict["scrobble"] = False
    return MessageContainer(NAME, L('Scrobbling is now stopped.'))

def ReadLog(last_line=None):
    log_path = LogPath()
    #Log("LogPath='%s'" % log_path)
    while Dict["scrobble"]:
        if last_line:
            ignore_lines = True
        else:
            ignore_lines = False
        for line in fileinput.input([log_path]):
            if ignore_lines:
                if line == last_line:
                    ignore_lines = False
                    continue
            else:
                Log(line)
                ### THIS IS WHERE THE CODE TO INTERPRET THE PMS LOG INFO WILL NEED TO GO ###
                last_line = line
        ReadLog(last_line)
    return 