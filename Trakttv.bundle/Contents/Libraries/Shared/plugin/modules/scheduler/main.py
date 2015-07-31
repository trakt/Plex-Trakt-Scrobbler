from plugin.models import SchedulerJob
from plugin.modules.core.base import Module
from plugin.modules.scheduler.handlers import SyncIntervalHandler

from datetime import datetime
from threading import Thread
import logging
import time

log = logging.getLogger(__name__)

HANDLERS = [
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
            SchedulerJob.due_at >= now
        ))

        if len(jobs) < 1:
            log.debug('No jobs found')
            return

        log.info('Processing %s job(s)', len(jobs))

        for job in jobs:
            self.process_job(job)

        log.info('Complete')

    def process_job(self, job):
        log.debug('Processing job: %r', job)
