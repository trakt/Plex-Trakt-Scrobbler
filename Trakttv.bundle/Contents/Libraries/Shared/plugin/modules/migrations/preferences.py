from plugin.core.environment import Environment
from plugin.modules.migrations.core.base import Migration
from plugin.preferences import OPTIONS_BY_PREFERENCE, Preferences

import logging

log = logging.getLogger(__name__)


class PreferencesMigration(Migration):
    def run(self):
        # Initialize preferences for administrator
        Preferences.initialize(account=1)

        # Migrate preferences to database
        for key in OPTIONS_BY_PREFERENCE.keys():
            Preferences.on_plex_changed(key, Environment.prefs[key], account=1)

            log.debug('Updated %r option in database', key)
