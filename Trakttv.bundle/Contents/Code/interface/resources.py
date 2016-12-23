from core.helpers import catch_errors
from plugin.core.constants import PLUGIN_PREFIX
from plugin.managers.account import AccountManager
from plugin.models import Account

import logging
import requests

log = logging.getLogger(__name__)


@route(PLUGIN_PREFIX + '/resources/cover')
@catch_errors
def Cover(account_id, refresh=None, *args, **kwargs):
    account = AccountManager.get(Account.id == account_id)

    if not account.trakt:
        return Redirect(R('art-default.png'))

    try:
        # Refresh trakt account details
        account.trakt.refresh()
    except Exception:
        log.warn('Unable to refresh trakt account details', exc_info=True)
        return Redirect(R('art-default.png'))

    if account.trakt.cover is None:
        return Redirect(R('art-default.png'))

    try:
        # Request cover image
        response = requests.get(account.trakt.cover)
    except Exception:
        log.warn('Unable to retrieve account cover', exc_info=True)
        return Redirect(R('art-default.png'))

    if response.status_code != 200:
        return Redirect(R('art-default.png'))

    return response.content


@route(PLUGIN_PREFIX + '/resources/thumb')
@catch_errors
def Thumb(account_id, refresh=None, *args, **kwargs):
    # Retrieve account
    account = AccountManager.get(Account.id == account_id)

    if not account.trakt:
        # TODO better account placeholder image
        return Redirect(R('icon-default.png'))

    # Retrieve thumb url
    thumb_url = account.thumb_url()

    if not thumb_url:
        # TODO better account placeholder image
        return Redirect(R('icon-default.png'))

    # Request thumb
    try:
        response = requests.get(thumb_url)
    except Exception:
        log.warn('Unable to retrieve account thumbnail', exc_info=True)
        return Redirect(R('icon-default.png'))

    if response.status_code != 200:
        return Redirect(R('icon-default.png'))

    return response.content
