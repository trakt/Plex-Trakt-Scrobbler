from plugin.models import SyncStatus, SyncResult
from plugin.preferences.options.core.base import SchedulerOption
from plugin.preferences.options.o_sync.constants import INTERVAL_LABELS_BY_KEY, INTERVAL_KEYS_BY_LABEL
from plugin.sync.core.enums import SyncMode

import logging

log = logging.getLogger(__name__)


class SyncIntervalOption(SchedulerOption):
    key = 'sync.interval'
    type = 'enum'

    choices = INTERVAL_LABELS_BY_KEY
    default = None

    group = ('Sync', 'Triggers')
    label = 'Interval'

    preference = 'sync_run_interval'

    def on_plex_changed(self, value, account=None):
        if value not in INTERVAL_KEYS_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = INTERVAL_KEYS_BY_LABEL[value]

        # Update database
        self.update(value, account, emit=False)
        return value

    @classmethod
    def get_last_result(cls, account, mode):
        status = (SyncStatus
            .select(
                SyncStatus.id
            )
            .where(
                SyncStatus.account == account,
                SyncStatus.mode == mode,
                SyncStatus.section == None
            )
            .first()
        )

        if status is None:
            return None

        return (SyncResult
            .select(
                SyncResult.started_at,
                SyncResult.ended_at
            )
            .where(
                SyncResult.status == status
            )
            .order_by(SyncResult.ended_at.desc())
            .first()
        )

    @classmethod
    def get_next(cls, job):
        if job.trigger is None:
            return None

        # Retrieve last full sync time
        last_result = cls.get_last_result(job.account, SyncMode.Full)

        if last_result is None:
            return job.next_at()

        return job.next_at(last_result.started_at)
