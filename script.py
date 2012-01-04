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
plexlog_path = config.get('Optional', 'plexlog_path')

# Will this always be current directory? maybe include something to get script location to use in path first?
logging.basicConfig(filename='Plex-Trakt-Scrobbler.log',format='%(asctime)s: %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p',level=logging.DEBUG)

def Log(string):
    # Probably want to pass through log type along with string. Can alsonuse logging.debug(string) and logging.warning(string)
    logging.info(string)
    print string.encode('utf-8')+"\n"
    
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
    if current_id != None:
        Log("Leaving Watch state")
        req = urllib2.Request("http://api.trakt.tv/movie/cancelwatching/"+api_key, auth_data, headers = { "Accept": "*/*", "User-Agent": user_agent})
        result = urllib2.urlopen(req)
        html = json.loads(result.read())

        Log("Status: " + html['status'])
        if html['status'] == "success":
            Log("Message: " + html['message'])
        else:
            Log("Message: " + html['error'])

        req = urllib2.Request("http://api.trakt.tv/show/cancelwatching/"+api_key, auth_data, headers = { "Accept": "*/*", "User-Agent": user_agent})
        result = urllib2.urlopen(req)
        html = json.loads(result.read())

        Log("Status: " + html['status'])
        if html['status'] == "success":
            Log("Message: " + html['message'])
        else:
            Log("Message: " + html['error'])

def add_to_trakt (video_type, title, year, duration, progress, guid):

    if progress < 85:
        kind = "watching"
    else:
        kind = "scrobble"

    if video_type == 'episode':
        video_type = 'show'
        m = re.search('com.plexapp.agents.thetvdb://([-a-z0-9\.]+)/([-a-z0-9\.]+)/([-a-z0-9\.]+)', guid)
        tvdb_id = m.group(1)
        season = m.group(2)
        episode = m.group(3)
        specific_data = urllib.urlencode({'tvdb_id': tvdb_id, 'season': season, 'episode': episode})
    else:
        m = re.search('com.plexapp.agents.imdb://(tt[-a-z0-9\.]+)', guid)
        imdb_id = m.group(1)
        specific_data = urllib.urlencode({'imdb_id': imdb_id})

    # define a Python data dictionary
    data = auth_data + "&" + urllib.urlencode({'title': title, 'progress': progress, 'duration': duration, 'plugin_version': plugin_version, 'media_center_version': version, 'year': year}) + "&" + specific_data

    Log("Make a call with this data: " + data)

    req = urllib2.Request("http://api.trakt.tv/" + video_type + "/" + kind + "/"+api_key, data, headers = { "Accept": "*/*", "User-Agent": user_agent})
    result = urllib2.urlopen(req)

    html = json.loads(result.read())

    Log("Status: " + html['status'])
    if html['status'] == "success":
        Log("Message: " + html['message'])
    else:
        Log("Message: " + html['error'])


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
        url = None
        try:
            m = re.search('progress on (?P<last>\w*?)\s', line)
            m2 = re.search('got played (?P<last>\w*?)\s', line)
            Log("Progress on "+m.group(1)+" is "+m2.group(1)+" ms")
            url = 'http://localhost:32400/library/metadata/'+m.group(1)
            progress = int(m2.group(1))
            Log(last_scrobbled_id)
        except: pass


        if url != None:
            #print url
            if duration != 0 and progress != 0:
                percent = round((float(progress)/duration)*100, 0)
            Log("percent "+str(percent))

            if last_commit < datetime.datetime.now() - datetime.timedelta(minutes=15) or current_id != m.group(1) or percent > 85.0:
                data = parse(urllib2.urlopen(url)).getroot()
                iter = data.findall("Video")
                for element in iter:
                    #print tostring(element)
                    title = element.attrib.get("title").encode('utf-8')
                    type = str(element.attrib.get("type"))
                    year = str(element.attrib.get("year"))
                    guid = str(element.attrib.get("guid"))
                    duration = int(element.attrib.get("duration"))
                    percent = round((float(progress)/duration)*100, 0)
                    #print "percent "+str(percent)
                    Log("Found the "+type+" "+title+" from "+year+", lets make a call to trakt.tv")
                    if last_scrobbled_id != m.group(1):
                        add_to_trakt(type, title, year, int(float(duration)/60000), percent, guid)
                    else:
                        Log("This is already scrobbled.")
                    last_commit = datetime.datetime.now()
                    current_id = m.group(1)
                    remaining = float(float(duration)-int(progress))/1000
                    if percent > 85.0:
                        last_scrobbled_id = current_id
                    # This won't work
                    #if remaining < 15*60 and percent > 85.0:
                    #    print "We are close to the end and have scrobbled so will pause for %s seconds." % str(remaining)
                    #    time.sleep(remaining)
                    #    current_id = None

        # Leave whatch state if not updated for 30 minutes
        if last_commit < datetime.datetime.now() - datetime.timedelta(minutes=30) and current_id != None:
            stop_watching()
            current_id = None

