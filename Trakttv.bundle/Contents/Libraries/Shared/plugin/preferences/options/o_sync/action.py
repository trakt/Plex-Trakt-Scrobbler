from plugin.preferences.options.core.base import Option
from plugin.preferences.options.o_sync.constants import ACTION_MODE_LABELS_BY_KEY
from plugin.sync.core.enums import SyncActionMode


class SyncActionModeOption(Option):
    key = 'sync.action.mode'
    type = 'enum'

    choices = ACTION_MODE_LABELS_BY_KEY
    default = SyncActionMode.Log  # TODO set to `SyncActionMode.Update` on release
    scope = 'server'

    group = ('Sync', 'Advanced')
    label = 'Action Mode'
