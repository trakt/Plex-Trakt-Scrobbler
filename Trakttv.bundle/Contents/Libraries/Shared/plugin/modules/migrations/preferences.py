from plugin.core.environment import Environment
from plugin.modules.migrations.core.base import Migration
from plugin.preferences import OPTIONS_BY_PKEY, Preferences

import logging

log = logging.getLogger(__name__)


class PreferencesMigration(Migration):
    def run(self):
        # Migrate preferences to database
        for key in OPTIONS_BY_PKEY.keys():
            Preferences.on_plex_changed(key, Environment.prefs[key])

            log.debug('Updated %r option in database', key)
