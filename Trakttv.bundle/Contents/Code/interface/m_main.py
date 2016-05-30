from core.helpers import pad_title
from interface.m_messages import Status as MessageStatus, ListMessages
from interface.m_sync import Accounts, AccountsMenu, ControlsMenu

from plugin.core.constants import PLUGIN_NAME, PLUGIN_ART, PLUGIN_ICON, PLUGIN_PREFIX, PLUGIN_VERSION
from plugin.core.environment import translate as _

import locale


@handler(PLUGIN_PREFIX, PLUGIN_NAME, thumb=PLUGIN_ICON, art=PLUGIN_ART)
def MainMenu():
    oc = ObjectContainer(no_cache=True)

    #
    # Messages
    #
    m_count, m_type = MessageStatus(viewed=False)

    if m_count > 0:
        oc.add(DirectoryObject(
            key=Callback(ListMessages, viewed=False),
            title=_("Messages (%s)") % locale.format("%d", m_count, grouping=True),
            thumb=R("icon-%s.png" % m_type)
        ))

    #
    # Sync
    #

    oc.add(DirectoryObject(
        key=Callback(ControlsMenu if Accounts.count() == 1 else AccountsMenu),
        title=_("Sync"),
        summary=_("Synchronize your libraries with Trakt.tv"),
        thumb=R("icon-sync.png")
    ))

    #
    # About
    #
    oc.add(DirectoryObject(
        key=Callback(AboutMenu),
        title=_("About"),
        thumb=R("icon-about.png")
    ))

    oc.add(PrefsObject(
        title=_("Preferences"),
        thumb=R("icon-preferences.png")
    ))

    return oc


@route(PLUGIN_PREFIX + '/about')
def AboutMenu():
    oc = ObjectContainer(
        title2=_("About")
    )

    oc.add(DirectoryObject(
        key=Callback(ListMessages, viewed=None),
        title=pad_title(_("Messages"))
    ))

    oc.add(DirectoryObject(
        key=Callback(AboutMenu),
        title=pad_title(_("Version: %s") % PLUGIN_VERSION)
    ))

    return oc
