from plugin.core.constants import PLUGIN_PREFIX
from plugin.managers import AccountManager
from plugin.models import Account

import requests


@route(PLUGIN_PREFIX + '/resources/cover')
def Cover(account_id):
    account = AccountManager.get(Account.id == account_id)

    if not account.trakt:
        return Redirect(R('art-default.png'))

    # Refresh trakt account details
    account.trakt.refresh()

    response = requests.get(account.trakt.cover)

    if response.status_code != 200:
        return Redirect(R('art-default.png'))

    return response.content


@route(PLUGIN_PREFIX + '/resources/thumb')
def Thumb(account_id):
    account = AccountManager.get(Account.id == account_id)

    if not account.trakt:
        # TODO better account placeholder image
        return Redirect(R('icon-default.png'))

    response = requests.get(account.thumb_url())

    if response.status_code != 200:
        return Redirect(R('art-default.png'))

    return response.content
