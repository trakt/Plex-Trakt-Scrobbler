from core.helpers import catch_errors, pad_title
from interface.m_messages import Status as MessageStatus, ListMessages
from interface.m_sync import Accounts, AccountsMenu, ControlsMenu

from plugin.core.constants import PLUGIN_NAME, PLUGIN_ART, PLUGIN_ICON, PLUGIN_PREFIX, PLUGIN_VERSION
from plugin.core.environment import translate as _
from plugin.managers.account import TraktAccountManager
from plugin.managers.m_trakt.authentication import TraktAuthenticationManager
from plugin.models import TraktAccount

import locale
import threading


@handler(PLUGIN_PREFIX, PLUGIN_NAME, thumb=PLUGIN_ICON, art=PLUGIN_ART)
@catch_errors
def MainMenu(*args, **kwargs):
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
    # Connect Trakt (Device Code Flow)
    #

    oc.add(DirectoryObject(
        key=Callback(ConnectTrakt),
        title=_("Connect Trakt"),
        summary=_("Connect or reauthorize a Trakt account"),
        thumb=R("icon-connection.png")
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


@route(PLUGIN_PREFIX + '/trakt/connect')
@catch_errors
def ConnectTrakt(account_id=None, *args, **kwargs):
    """Connect Trakt using Device Code Flow without requiring Preferences."""
    oc = ObjectContainer(
        title2=_("Connect Trakt"),
        no_cache=True
    )

    accounts = TraktAccountManager.get.all()

    if account_id is not None:
        try:
            trakt_account = TraktAccountManager.get(TraktAccount.id == int(account_id))
        except Exception:
            trakt_account = accounts.first()
    else:
        trakt_account = accounts.first()

    if trakt_account is None:
        oc.message = _("No Trakt account found. Create/link a Trakt account first.")
        return oc

    try:
        device_authorization = TraktAuthenticationManager.request_device_code()
    except Exception as ex:
        oc.message = _("Unable to start Trakt Device Code Flow: %s") % ex
        return oc

    instructions = TraktAuthenticationManager.format_device_instructions(device_authorization)

    # Start polling in background; user needs instructions while waiting.
    thread = threading.Thread(
        target=TraktAuthenticationManager.authenticate_account_with_device,
        args=(trakt_account, device_authorization),
        name='TraktDeviceAuthorization',
    )
    thread.daemon = True
    thread.start()

    oc.message = instructions
    return oc

@route(PLUGIN_PREFIX + '/about')
@catch_errors
def AboutMenu(*args, **kwargs):
    oc = ObjectContainer(
        title2=_("About")
    )

    oc.add(DirectoryObject(
        key=Callback(ListMessages, days=None, viewed=None),
        title=pad_title(_("Messages"))
    ))

    oc.add(DirectoryObject(
        key=Callback(AboutMenu),
        title=pad_title(_("Version: %s") % PLUGIN_VERSION)
    ))

    return oc
