from core.cache import CacheManager
from core.helpers import pad_title
from core.plugin import ART, NAME, ICON
from interface.sync_menu import AccountsMenu, ControlsMenu

from plugin.core.constants import PLUGIN_PREFIX, PLUGIN_VERSION
from plugin.managers import AccountManager


@handler(PLUGIN_PREFIX, NAME, thumb=ICON, art=ART)
def MainMenu():
    oc = ObjectContainer(no_cache=True)

    num_accounts = AccountManager.get.all().count()

    oc.add(DirectoryObject(
        key=Callback(AccountsMenu if num_accounts > 1 else ControlsMenu),
        title=L("Sync"),
        summary=L("Sync the Plex library with trakt.tv"),
        thumb=R("icon-sync.png")
    ))

    oc.add(DirectoryObject(
        key=Callback(AboutMenu),
        title=L("About"),
        thumb=R("icon-about.png")
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
        key=Callback(CacheStatisticsMenu),
        title=pad_title("Cache Statistics")
    ))

    oc.add(DirectoryObject(
        key=Callback(AboutMenu),
        title=pad_title("Version: %s" % PLUGIN_VERSION)
    ))

    return oc


@route(PLUGIN_PREFIX + '/about/cache')
def CacheStatisticsMenu():
    oc = ObjectContainer(title2="Cache Statistics")

    for item in CacheManager.statistics():
        oc.add(DirectoryObject(
            key='',
            title=pad_title("[%s] Cache Size: %s, Store Size: %s" % item)
        ))

    return oc
