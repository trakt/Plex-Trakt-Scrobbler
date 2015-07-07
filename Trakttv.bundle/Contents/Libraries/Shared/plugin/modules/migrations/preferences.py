from plugin.models import Account
from plugin.modules.migrations.core.base import Migration
from plugin.preferences import Preferences

import logging

log = logging.getLogger(__name__)


class PreferencesMigration(Migration):
    def run(self):
        # Migrate server preferences
        Preferences.initialize()
        Preferences.migrate()

        # Try migrate administrator preferences
        try:
            Preferences.initialize(account=1)
            Preferences.migrate(account=1)
        except Account.DoesNotExist:
            log.debug('Unable to migrate administrator preferences, no account found')
