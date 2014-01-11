from core.helpers import pad_title
from core.plugin import ART, NAME, ICON, PLUGIN_VERSION
from interface.sync_menu import SyncMenu


@handler('/applications/trakttv', NAME, thumb=ICON, art=ART)
def MainMenu():
    oc = ObjectContainer()

    oc.add(DirectoryObject(
        key=Callback(SyncMenu),
        title=L("Sync"),
        summary=L("Sync the Plex library with Trakt.tv")
    ))

    oc.add(DirectoryObject(
        key=Callback(AboutMenu),
        title=L("About")
    ))

    oc.add(PrefsObject(
        title="Preferences",
        summary="Configure how to connect to Trakt.tv",
        thumb=R("icon-preferences.png")
    ))

    return oc


@route('/applications/trakttv/about')
def AboutMenu():
    oc = ObjectContainer(title2="About")

    oc.add(DirectoryObject(
        key='',
        title=pad_title("Version: %s" % PLUGIN_VERSION)
    ))

    return oc
