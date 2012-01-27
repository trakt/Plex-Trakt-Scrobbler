#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import urllib
from elementtree.ElementTree import parse, tostring
import time, os, datetime
import hashlib
import simplejson as json
import urllib2
import signal
import ConfigParser
import logging

if sys.platform == 'win32':
    import winpaths

path = os.path.dirname(os.path.abspath( __file__ ))
config = ConfigParser.RawConfigParser()
config.read(path + '/config.ini')
trakt_username = config.get('Trakt', 'username')
trakt_password = config.get('Trakt', 'password')
trakt_password = hashlib.sha1(trakt_password).hexdigest()
plexlog_path = config.get('Optional', 'plexlog_path')

# Will this always be current directory? maybe include something to get script location to use in path first?
logging.basicConfig(filename='Plex-Trakt-Scrobbler.log',format='%(asctime)s: %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p',level=logging.DEBUG)

def Log(string):
    # Probably want to pass through log type along with string. Can alsonuse logging.debug(string) and logging.warning(string)
    logging.info(string)
    print string
    
plugin_version = "0.2"
# Path to your PMS Server log file
if plexlog_path != '':
    filename = plexlog_path
elif sys.platform == 'win32':
    filename = os.path.join(winpaths.get_local_appdata(), 'Plex Media Server\Logs\Plex Media Server.log')
elif sys.platform == 'darwin':
    filename = os.path.join(os.environ['HOME'], 'Library/Logs/Plex Media Server.log')
# Using startswith for linux, as read about new kernel reporting as linux3 rather than linux2
elif sys.platform.startswith('linux'):
    filename = '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log'
else:
    Log('OS not detected correctly, please specify Plex log path in config.ini')

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

url = 'http://localhost:32400/'
api_key = 'ba5aa61249c02dc5406232da20f6e768f3c82b28'

createSha1 = hashlib.sha1(trakt_password)
auth_data = "username=" + trakt_username + "&password=" + createSha1.hexdigest()

data = parse(urllib2.urlopen(url)).getroot()
version = str(data.attrib.get("version"))
platform = str(data.attrib.get("platform"))
platformVersion = str(data.attrib.get("platformVersion"))
filename = str(os.path.abspath(filename))
# Need to be older then default check value
last_commit = datetime.datetime.now()
current_id = None
progress = 0
duration = 0
percent = 0
last_scrobbled_id = 0

if os.path.isfile(filename) == False:
    Log('Plex Log file not found')
    sys.exit()

Log("Started monitoring...")
Log("Running on "+platform+" "+platformVersion+" with PMS Version "+version)
Log("Plugin version: "+plugin_version)
Log("Monitoring the log at "+filename)
Log("PMS running at "+url)
Log("trakt.tv username "+trakt_username)

user_agent = "PMS Scrobbler for trakt.tv/"+plugin_version+" (compatible; "+platformVersion+"; "+platform+")"

def signal_handler(signal, frame):
    Log('Down for a halt')
    stop_watching()

    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def stop_watching():
    Log("Leaving Watch state")
    
    status = talk_to_trakt('movie/cancelwatching', {'username' : trakt_username, 'password' : trakt_password})
    
    Log("Trakt responded with: %s " % status['message'])

def watch_or_scrobble(item_id, progress):
    # Function to add what currently is playing to trakt, decide o watch or scrobble
    values = get_metadata_from_pms(item_id)
    progress = int(float(progress)/60000)
    values['progress'] = round((float(progress)/values['duration'])*100, 0)
    # Add username and password to values
    values['username'] = trakt_username
    values['password'] =  trakt_password

    # Just for debugging
    #Log(values)
    
    if 'tvdb_id' in values:
        action = 'show/'
    elif 'imdb_id' in values:
        action = 'movie/'
    else:
        # Todo
        return {'status' : False, 'message' : 'Not a movie or TV-show'}
    
    if values['progress'] > 85.0:
        Log('We will scrobble it')
        action += 'scrobble'
    else:
        Log('We will watch it')
        #action += 'watching'
        return {'status' : False, 'message' : 'not implmented yeat'}
    

    result = talk_to_trakt(action, values)
    result['action'] = action
    return result

def talk_to_trakt(action, values):
    # Function to talk to the trakt.tv api
    data_url = TRAKT_URL % action
    
    try:
        req = urllib2.Request(data_url, urllib.urlencode(values))
        result = urllib2.urlopen(req)
        result = json.loads(result.read())
        #Log(result)

    except urllib2.HTTPError, e:
        result = {'status' : 'failure', 'error' : responses[e.code][1]}
    except urllib2.URLError, e:
        return {'status' : 'failure', 'error' : e.reason[0]}

    if result['status'] == 'success':
        Log('Trakt responded with: %s' % result['message'])
        return {'status' : True, 'message' : result['message']}
    else:
        Log('Trakt responded with: %s' % result['error'])
        return {'status' : False, 'message' : result['error']}

def get_metadata_from_pms(item_id):
    # Prepare a dict that contains all the metadata required for trakt.
    host = "localhost"

    if host.find(':') == -1:
        host += ':32400'

    pms_url = PMS_URL % (host, 'metadata/' + str(item_id))
    #Log(pms_url)
    try:
        req = urllib2.Request(pms_url)
        data = parse(urllib2.urlopen(req)).getroot()
        xml_content = data.findall("Video")
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
    except urllib2.HTTPError, e:
        Log('Failed to connect to %s.' % pms_url)
        return {'status' : False, 'message' : responses[e.code][1]}
    except urllib2.URLError, e:
        Log('Failed to connect to %s.' % pms_url)
        return {'status' : False, 'message' : e.reason[0]}


#Set the filename and open the file
file = open(filename,'r')

#Find the size of the file and move to the end
st_results = os.stat(filename)
st_size = st_results[6]
file.seek(st_size)

while 1:
    where = file.tell()
    line = file.readline()
    if not line:
        time.sleep(1)
        file.seek(where)
    else:
        #print line, # already has newline
        item_progress = None
        item_id = None
        try:
            m = re.search('progress on (?P<last>\w*?)\s', line)
            m2 = re.search('got played (?P<last>\w*?)\s', line)
            Log("Progress on "+m.group(1)+" is "+m2.group(1)+" ms")
            item_progress = m2.group(1)
            item_id = m.group(1)
        except: pass
        


        if item_progress != None and item_id != None and last_scrobbled_id != item_id:
            status = watch_or_scrobble(item_id, item_progress)
            
            Log('Response: %s' % status['message'])
            
            if status['status'] and 'scrobble' in status['action']:
                last_scrobbled_id = item_id