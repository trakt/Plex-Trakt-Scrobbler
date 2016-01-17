from core.helpers import pad_title
from core.plugin import ART, NAME, ICON
from interface.m_messages import Status as MessageStatus, ListMessages
from interface.m_sync import Accounts, AccountsMenu, ControlsMenu

from plugin.core.constants import PLUGIN_PREFIX, PLUGIN_VERSION

import locale


@handler(PLUGIN_PREFIX, NAME, thumb=ICON, art=ART)
def MainMenu():
    oc = ObjectContainer(no_cache=True)

    #
    # Messages
    #
    m_count, m_type = MessageStatus(viewed=False)

    if m_count > 0:
        oc.add(DirectoryObject(
            key=Callback(ListMessages, viewed=False),
            title="Messages (%s)" % locale.format("%d", m_count, grouping=True),
            thumb=R("icon-%s.png" % m_type)
        ))

    #
    # Sync
    #

    oc.add(DirectoryObject(
        key=Callback(ControlsMenu if Accounts.count() == 1 else AccountsMenu),
        title=L("Sync"),
        summary=L("Sync the Plex library with trakt.tv"),
        thumb=R("icon-sync.png")
    ))

    #
    # About
    #
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
        key=Callback(ListMessages, viewed=None),
        title=pad_title("Messages")
    ))

    oc.add(DirectoryObject(
        key=Callback(AboutMenu),
        title=pad_title("Version: %s" % PLUGIN_VERSION)
    ))

    return oc
