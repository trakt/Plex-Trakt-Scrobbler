from plugin.core.environment import translate as _
from plugin.preferences.options.core.base import SchedulerOption
from plugin.preferences.options.o_sync.constants import INTERVAL_LABELS_BY_KEY
from plugin.sync.core.enums import SyncInterval

import logging

log = logging.getLogger(__name__)


class BackupMaintenanceIntervalOption(SchedulerOption):
    key = 'backup.interval'
    type = 'enum'

    choices = INTERVAL_LABELS_BY_KEY
    default = SyncInterval.D1
    scope = 'server'

    group = (_('Backups'),)
    label = _('Maintenance Interval')
    order = 10
