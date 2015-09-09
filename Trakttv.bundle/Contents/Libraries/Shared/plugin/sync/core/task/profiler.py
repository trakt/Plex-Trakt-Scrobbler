import elapsed
import logging

log = logging.getLogger(__name__)


class SyncProfiler(object):
    def __init__(self, task):
        self.task = task

    @staticmethod
    def log_report():
        log.debug('Profiler Report\n%s', '\n'.join(elapsed.format_report()))
