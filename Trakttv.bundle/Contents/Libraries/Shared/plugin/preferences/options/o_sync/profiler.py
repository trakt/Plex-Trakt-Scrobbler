from plugin.preferences.options.core.base import SimpleOption
from plugin.preferences.options.o_sync.constants import PROFILER_MODE_LABELS_BY_KEY
from plugin.sync.core.enums import SyncProfilerMode


class SyncProfilerOption(SimpleOption):
    key = 'sync.profiler'
    type = 'enum'

    choices = PROFILER_MODE_LABELS_BY_KEY
    default = SyncProfilerMode.Disabled
    scope = 'server'

    group = ('Advanced', 'Sync')
    label = 'Profiler'
    order = 121
