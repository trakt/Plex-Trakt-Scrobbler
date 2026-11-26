# -*- coding: utf-8 -*-

from plugin.core.environment import translate as _
from plugin.managers.account import TraktAccountManager
from plugin.managers.m_trakt.authentication import TraktAuthenticationManager
from plugin.models import TraktAccount
from plugin.preferences.options.core.base import SimpleOption

import logging
import threading

log = logging.getLogger(__name__)


class ConnectTraktOption(SimpleOption):
    """
    Connect Trakt — Device Code Flow.

    Replaces old PIN input. Temporary device authorization is not persisted.
    Existing account records/Plex associations are preserved.
    """

    type = 'string'

    key = 'connect_trakt'
    preference = 'connect_trakt'

    group = (_('Authentication'), )
    label = _('Connect Trakt')

    default = ''

    def on_database_changed(self, value, account=None):
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account):
        # Empty field does nothing. Non-empty is a Connect Trakt trigger.
        if not value:
            return None

        # Avoid re-triggering on returned instruction strings.
        if isinstance(value, basestring) and value.startswith('Connect Trakt'):
            return value

        # Retrieve administrator account
        trakt_account = TraktAccountManager.get(TraktAccount.account == account)

        # Request temporary device authorization. Not persisted as account credential.
        device_authorization = TraktAuthenticationManager.request_device_code()
        instructions = TraktAuthenticationManager.format_device_instructions(device_authorization)

        log.info('[Trakt] Device authorization initiated')
        log.info('[Trakt] Waiting for user authorization')

        # Poll in background; user needs instructions while waiting.
        thread = threading.Thread(
            target=TraktAuthenticationManager.authenticate_account_with_device,
            args=(trakt_account, device_authorization),
            name='TraktDeviceAuthorization',
        )
        thread.daemon = True
        thread.start()

        # Display:
        # Connect Trakt
        # 1. Open: [verification_url]
        # 2. Enter code: ABCD-EFGH
        # Waiting for authorization...
        self._update_preference(instructions, account)
        return instructions


# Python 2 compatibility
try:
    basestring
except NameError:
    basestring = str
