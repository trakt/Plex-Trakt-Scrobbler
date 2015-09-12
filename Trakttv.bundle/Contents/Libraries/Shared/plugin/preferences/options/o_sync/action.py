from plugin.preferences.options.core.base import SimpleOption
from plugin.preferences.options.o_sync.constants import ACTION_MODE_LABELS_BY_KEY
from plugin.sync.core.enums import SyncActionMode


class SyncActionOption(SimpleOption):
    key = 'sync.action.mode'
    type = 'enum'

    choices = ACTION_MODE_LABELS_BY_KEY
    default = None
    scope = 'server'

    group = ('Advanced', 'Sync')
    label = 'Action'
    order = 120

    @property
    def value(self):
        value = super(SyncActionOption, self).value

        if value is None:
            return SyncActionMode.Update

        return value

