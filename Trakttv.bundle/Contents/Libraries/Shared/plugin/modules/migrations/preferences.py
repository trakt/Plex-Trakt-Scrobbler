from plugin.modules.migrations.core.base import Migration
from plugin.preferences import Preferences


class PreferencesMigration(Migration):
    def run(self):
        # Initialize preferences for administrator
        Preferences.initialize(account=1)
        Preferences.initialize()

        # Migrate preferences to database
        Preferences.migrate(account=1)
        Preferences.migrate()
