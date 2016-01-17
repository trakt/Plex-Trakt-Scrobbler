from plugin.sync.core.enums import SyncMode
from plugin.sync.modes.core.base import Mode

import logging

log = logging.getLogger(__name__)


class Base(Mode):
    mode = SyncMode.Pull

    def step(self, pending, data, key):
        if key not in pending[data]:
            return

        # Remove from `pending` dictionary
        del pending[data][key]
