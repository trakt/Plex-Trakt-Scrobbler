from core.helpers import pad_title, get_pref
from core.plugin import ART, NAME, ICON, PLUGIN_PREFIX, PLUGIN_VERSION
from interface.sync_menu import SyncMenu


@handler(PLUGIN_PREFIX, NAME, thumb=ICON, art=ART)
def MainMenu():
    oc = ObjectContainer(no_cache=True)

    if not get_pref('valid'):
        oc.add(DirectoryObject(
            key=PLUGIN_PREFIX,
            title=L("Error: Authentication failed"),
        ))

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


@route(PLUGIN_PREFIX + '/about')
def AboutMenu():
    oc = ObjectContainer(title2="About")

    oc.add(DirectoryObject(
        key=Callback(AboutMenu),
        title=pad_title("Version: %s" % PLUGIN_VERSION)
    ))

    return oc
