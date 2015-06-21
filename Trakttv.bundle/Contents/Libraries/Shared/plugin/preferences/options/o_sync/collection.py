from plugin.preferences.options.core.base import Option
from plugin.preferences.options.o_sync.constants import MODES_BY_LABEL, MODES_BY_KEY

import logging

log = logging.getLogger(__name__)


class SyncCollection(Option):
    key = 'sync.collection.mode'
    type = 'enum'

    choices = MODES_BY_KEY
    default = None

    group = ('Sync', 'Collection')
    label = 'Mode'

    preference = 'sync_collection'

    @classmethod
    def on_plex_changed(cls, value, account=None):
        if value not in MODES_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = MODES_BY_LABEL[value]

        # Update database
        cls.update(value, account)
        return value


class SyncCleanCollection(Option):
    key = 'sync.collection.clean'
    type = 'boolean'

    default = False

    group = ('Sync', 'Collection')
    label = 'Clean collection'

    preference = 'sync_clean_collection'

    @classmethod
    def on_plex_changed(cls, value, account=None):
        # Update database
        cls.update(value, account)
        return value
