from plugin.models import SyncResult
from plugin.modules.scheduler.handlers.core.base import Handler
from plugin.preferences.options import SyncIntervalOption
from plugin.sync.core.enums import SyncMode
from plugin.sync.core.exceptions import QueueError
from plugin.sync.main import Sync

from datetime import datetime
import logging

log = logging.getLogger(__name__)


class SyncIntervalHandler(Handler):
    key = 'sync.interval'

    def check(self, job):
        last_result = SyncIntervalOption.get_last_result(job.account, SyncMode.Full)

        if last_result is None or last_result.started_at <= job.due_at:
            return True

        # Re-schedule job
        job.due_at = job.next_at(last_result.started_at)

        log.debug('Job re-scheduled to %r', job.due_at)

        # Check if a trigger is required
        if job.due_at <= datetime.utcnow():
            return True

        # Trigger ignored, update job
        job.save()

        log.debug('Ignoring scheduled sync interval (already triggered)')
        return False

    def run(self, job):
        # Ensure sync hasn't already been triggered
        if not self.check(job):
            return False

        try:
            # Queue sync
            Sync.queue(
                account=job.account,
                mode=SyncMode.Full,

                priority=100,
                trigger=SyncResult.Trigger.Schedule
            )
        except QueueError as ex:
            log.info('Queue error: %s', ex)
        except Exception as ex:
            log.error('Unable to queue sync: %s', ex, exc_info=True)

        return True
