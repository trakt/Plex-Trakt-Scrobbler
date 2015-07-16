from plugin.core.constants import PLUGIN_PREFIX
from plugin.managers import AccountManager
from plugin.models import Account

from requests import RequestException
import logging
import requests

log = logging.getLogger(__name__)


@route(PLUGIN_PREFIX + '/resources/cover')
def Cover(account_id, refresh=None):
    account = AccountManager.get(Account.id == account_id)

    if not account.trakt:
        return Redirect(R('art-default.png'))

    try:
        # Refresh trakt account details
        account.trakt.refresh()
    except RequestException:
        log.warn('Unable to refresh trakt account details', exc_info=True)
        return Redirect(R('art-default.png'))

    if account.trakt.cover is None:
        return Redirect(R('art-default.png'))

    try:
        # Request cover image
        response = requests.get(account.trakt.cover)
    except RequestException:
        log.warn('Unable to retrieve account cover', exc_info=True)
        return Redirect(R('art-default.png'))

    if response.status_code != 200:
        return Redirect(R('art-default.png'))

    return response.content


@route(PLUGIN_PREFIX + '/resources/thumb')
def Thumb(account_id, refresh=None):
    account = AccountManager.get(Account.id == account_id)

    if not account.trakt:
        # TODO better account placeholder image
        return Redirect(R('icon-default.png'))

    try:
        response = requests.get(account.thumb_url())
    except RequestException:
        log.warn('Unable to retrieve account thumbnail', exc_info=True)
        return Redirect(R('icon-default.png'))

    if response.status_code != 200:
        return Redirect(R('icon-default.png'))

    return response.content
