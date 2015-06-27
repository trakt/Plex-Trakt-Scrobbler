from plugin.managers import TraktAccountManager
from plugin.models import TraktAccount
from plugin.preferences.options.core.base import Option

import logging

log = logging.getLogger(__name__)


class Pin(Option):
    type = 'string'

    group = ('Authentication', )
    label = 'Authentication PIN'

    preference = 'pin'

    def on_database_changed(self, value, account=None):
        # Update preference
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account):
        if not value:
            # Ignore empty PIN field
            return None

        # Retrieve administrator account
        trakt_account = TraktAccountManager.get(TraktAccount.account == account)

        # Update administrator authorization
        if not TraktAccountManager.update.from_pin(trakt_account, value):
            log.warn('Unable to update account')
            return None

        return value
