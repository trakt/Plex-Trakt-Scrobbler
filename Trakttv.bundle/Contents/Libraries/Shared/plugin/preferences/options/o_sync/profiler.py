from plugin.core.environment import translate as _
from plugin.preferences.options.core.base import SimpleOption
from plugin.preferences.options.core.description import Description
from plugin.preferences.options.o_sync.constants import PROFILER_MODE_LABELS_BY_KEY
from plugin.sync.core.enums import SyncProfilerMode


class SyncProfilerOption(SimpleOption):
    key = 'sync.profiler'
    type = 'enum'

    choices = PROFILER_MODE_LABELS_BY_KEY
    default = SyncProfilerMode.Disabled
    scope = 'server'

    group = (_('Advanced'), _('Sync'))
    label = _('Profiler')
    description = Description(
        _("Profiler to use for performance analysis during syncs"), [
            (_("Basic"), _(
                "Basic per-method elapsed time reports *([elapsed.py](https://github.com/fuzeman/elapsed.py))*"
            )),
            (_("Disabled"), _(
                "Disable sync profiling"
            ))
        ]
    )
    order = 121
