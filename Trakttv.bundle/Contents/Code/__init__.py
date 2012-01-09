import logsucker
import hashlib

APPLICATIONS_PREFIX = "/applications/trakttv"

NAME = L('Title')

# make sure to replace artwork with what you want
# these filenames reference the example files in
# the Contents/Resources/ folder in the bundle
ART  = 'art-default.jpg'
ICON = 'icon-default.png'
PMS_URL = 'http://%s/library/sections/'
TRAKT_URL = 'http://api.trakt.tv/%s/ba5aa61249c02dc5406232da20f6e768f3c82b28'


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

def ValidatePrefs():
    u = Prefs['username']
    p = Prefs['password']
    ## do some checks and return a
    ## message container
    
    values = {}
    values['username'] = u
    values['password'] = hashlib.sha1(p).hexdigest()
    
    
    if talk_to_trakt('account/test', values):
        return MessageContainer(
            "Success",
            "Valid username and password provided"
        )
    else:
        return MessageContainer(
            "Error",
            "You need to provide a valid username and password"
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
    title = "Dummy"
    key = "1"
    

    url = GetPmsHost() + key + '/refresh'
    update = HTTP.Request(url, cacheTime=1).content

    if title == 'All sections':
        return MessageContainer(title, 'All sections will be updated!')
    elif len(key) > 1:
        return MessageContainer(title, 'All chosen sections will be updated!')
    else:
        return MessageContainer(title, 'Section "' + title + '" will be updated!')

def GetPmsHost():
  host = Prefs['pms_host']

  if host.find(':') == -1:
    host += ':32400'

  return PMS_URL % (host)

def talk_to_trakt(action, values):
    # Function to talkt to the plex api
    data_url = TRAKT_URL % action

    try:
        result = JSON.ObjectFromURL(data_url, values=values)
        Log(result)

        if result['status'] == 'success':
            Log('Trakt responded with: %s' % result['message'])
            return True
        else:
            Log('Trakt responded with: %s' % result['error'])
            return False
    except:
        Log('Could not talk to Trakt.tv')
        return False
