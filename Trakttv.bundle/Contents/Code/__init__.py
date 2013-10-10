from plugin import ART, NAME, ICON
from pms import PMS
from scrobbler import Scrobbler
from sync import SyncTrakt, ManuallySync
from trakt import Trakt


class Main:
    def __init__(self):
        self.scrobbler = Scrobbler()

        if not 'nowPlaying' in Dict:
            Dict['nowPlaying'] = dict()

        Main.update_config()

    @staticmethod
    def update_config():
        if Prefs['start_scrobble'] and Prefs['username'] is not None:
            Log('Autostart scrobbling')
            Dict["scrobble"] = True
        else:
            Dict["scrobble"] = False

        if Prefs['new_sync_collection'] and Prefs['username'] is not None:
            Log('Automatically sync new Items to Collection')
            Dict["new_sync_collection"] = True
        else:
            Dict["new_sync_collection"] = False

    def start(self):
        if Prefs['sync_startup'] and Prefs['username'] is not None:
            Log('Will autosync in 1 minute')
            Thread.CreateTimer(60, SyncTrakt)

        # Get current server version and save it to dict.
        server_version = PMS.get_server_version()
        if server_version:
            Log('Server Version is %s' % server_version)
            Dict['server_version'] = server_version

        Thread.Create(self.scrobbler.listen)


def Start():
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)

    main = Main()
    main.start()


def ValidatePrefs():
    if Prefs['username'] is None:
        return MessageContainer("Error", "No login information entered.")

    if not Prefs['sync_watched'] and not Prefs['sync_ratings'] and not Prefs['sync_collection']:
        return MessageContainer("Error", "At least one sync type need to be enabled.")

    if not Prefs['start_scrobble']:
        Dict["scrobble"] = False

    status = Trakt.request('account/test')

    if status['status']:
        Main.update_config()

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

    oc.add(DirectoryObject(
        key=Callback(ManuallySync),
        title=L("Sync"),
        summary=L("Sync the Plex library with Trakt.tv"),
        thumb=R("icon-sync.png")
    ))

    oc.add(PrefsObject(
        title="Preferences",
        summary="Configure how to connect to Trakt.tv",
        thumb=R("icon-preferences.png")
    ))

    return oc
