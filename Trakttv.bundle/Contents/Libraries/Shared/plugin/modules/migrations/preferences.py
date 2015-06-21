from plugin.models import Account
from plugin.modules.migrations.core.base import Migration
from plugin.preferences import Preferences

import logging

log = logging.getLogger(__name__)


class PreferencesMigration(Migration):
    def run(self):
        # Ensure "server" account exists
        try:
            Account.get(Account.id == 1)
        except Account.DoesNotExist:
            Account.create()

        # Initialize preferences for administrator
        Preferences.initialize(account=1)

        # Migrate preferences to database
        Preferences.migrate(account=1)
        Preferences.migrate()
