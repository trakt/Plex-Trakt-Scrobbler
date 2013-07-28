from plugin import ART, NAME, ICON
from scrobbler import Scrobble
from sync import SyncTrakt, ManuallySync
from trakt import talk_to_trakt


def Start():

    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)

    if Prefs['start_scrobble'] and Prefs['username'] is not None:
        Log('Autostart scrobbling')
        Dict["scrobble"] = True
        Thread.Create(Scrobble)

    if Prefs['sync_startup'] and Prefs['username'] is not None:
        Log('Will autosync in 1 minute')
        Thread.CreateTimer(60, SyncTrakt)


def ValidatePrefs():
    u = Prefs['username']
    p = Prefs['password']

    if Prefs['username'] is None:
        return MessageContainer("Error", "No login information entered.")

    if not Prefs['sync_watched'] and not Prefs['sync_ratings'] and not Prefs['sync_collection']:
        return MessageContainer("Error", "At least one sync type need to be enabled.")

    if not Prefs['start_scrobble']:
        Dict["scrobble"] = False

    status = talk_to_trakt('account/test', {'username' : u, 'password' : Hash.SHA1(p)})

    if status['status']:

        if Prefs['start_scrobble']:
            Log('Autostart scrobbling')
            Dict["scrobble"] = True
            Thread.Create(Scrobble)

        return MessageContainer(
            "Success",
            "Trakt responded with: %s " % status['message']
        )
    else:
        return MessageContainer(
            "Error",
            "Trakt responded with: %s " % status['message']
        )


@handler('/applications/trakttv', NAME, thumb=ICON, art=ART)
def MainMenu():

    oc = ObjectContainer()

    # Test if the user has the correct settings in the PMS.
    for setting in XML.ElementFromURL('http://localhost:32400/:/prefs', errors='ignore').xpath('//Setting'):
        if setting.get('id') == 'logDebug' and setting.get('value') != 'true':
            oc.add(DirectoryObject(key=Callback(FixLogging), title=L("Warning: Incorrect logging settings!"), summary=L("The logging is disabled on the Plex Media Server scrobbling won't work, click here to enable it."), thumb=R("icon-error.png")))
            Log('Logging is currently disabled')

    oc.add(DirectoryObject(key=Callback(ManuallySync), title=L("Sync"), summary=L("Sync the Plex library with Trakt.tv"), thumb=R("icon-sync.png")))

    oc.add(PrefsObject(title="Preferences", summary="Configure how to connect to Trakt.tv", thumb=R("icon-preferences.png")))
    return oc


@route('/applications/trakttv/fixlogging')
def FixLogging():
    try:
        HTTP.Request('http://localhost:32400/:/prefs?logDebug=1', method='PUT')
        return MessageContainer("Success", "The logging preferences is changed.")
    except:
        return MessageContainer("Error", "Failed to change the preferences on the Plex Media Server.")
