from core.plugin import ART, NAME, ICON
from interface.sync_menu import SyncMenu


@handler('/applications/trakttv', NAME, thumb=ICON, art=ART)
def MainMenu():
    oc = ObjectContainer()

    oc.add(DirectoryObject(
        key=Callback(SyncMenu),
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
