from plugin.sync.core.enums import SyncProfilerMode

import elapsed
import logging

log = logging.getLogger(__name__)


class SyncProfiler(object):
    def __init__(self, task):
        self.task = task

        self.mode = None

    def load(self):
        # Retrieve current mode
        self.mode = self.task.configuration['sync.profiler']

        # Setup profilers
        if self.mode == SyncProfilerMode.Basic:
            # Enable elapsed.py
            elapsed.setup(enabled=True)

            log.info('Enabled profiler: elapsed.py (basic)')
        else:
            # Ensure elapsed.py is disabled
            elapsed.setup(enabled=False)

    def log_report(self):
        if self.mode == SyncProfilerMode.Basic:
            # Display elapsed.py report
            log.debug('Profiler Report\n%s', '\n'.join(elapsed.format_report()))
