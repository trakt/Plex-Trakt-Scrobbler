from plugin.models import SchedulerJob
from plugin.modules.core.base import Module
from plugin.modules.scheduler.handlers import BackupMaintenanceIntervalHandler, SyncIntervalHandler

from datetime import datetime
from threading import Thread
import logging
import time

log = logging.getLogger(__name__)

HANDLERS = [
    BackupMaintenanceIntervalHandler,
    SyncIntervalHandler
]


class Scheduler(Module):
    __key__ = 'scheduler'

    handlers = dict([
        (h.key, h) for h in HANDLERS
        if h.key is not None
    ])

    def __init__(self):
        self._running = False

        self._thread = Thread(target=self.run, name='Scheduler')
        self._thread.daemon = True

    def start(self):
        self._running = True
        self._thread.start()

        log.debug('Started')

    def run(self):
        while self._running:
            # Process batch
            self.process()

            # Wait 60s before re-checking
            time.sleep(60)

    def process(self):
        # Retrieve due jobs
        now = datetime.utcnow()

        jobs = list(SchedulerJob.select().where(
            SchedulerJob.due_at <= now
        ))

        if len(jobs) < 1:
            return

        log.debug('Processing %s job(s)', len(jobs))

        for job in jobs:
            # Process job
            update = self.process_job(job)

            # Update job status
            self.finish(job, update)

        log.debug('Complete')

    def process_job(self, job):
        if job.account.deleted:
            # Ignore scheduled jobs for deleted accounts
            return True

        log.info('Running job: %r', job)

        # Retrieve handler for job
        handler = self.handlers.get(job.task_key)

        if handler is None:
            log.info('Deleting job with unknown task key: %r', job.task_key)
            job.delete_instance()
            return False

        # Run handler
        try:
            h = handler()

            return h.run(job)
        except Exception as ex:
            log.error('Exception raised in job handler: %s', ex, exc_info=True)
            return True

    @staticmethod
    def finish(job, update=True):
        if not update:
            return

        # Update status
        job.ran_at = datetime.utcnow()
        job.due_at = job.next_at()

        # Save changes
        job.save()
