from plugin.sync.core.enums import SyncMode
from plugin.sync.modes.core.base import Mode

import logging

log = logging.getLogger(__name__)


class FastPull(Mode):
    mode = SyncMode.FastPull

    def run(self):
        # Fetch changes from trakt.tv
        self.trakt.refresh()

        # Quick pull - applies any changes to your trakt profile, won't directly compare changes between plex & trakt.
        for (media, data), changes in self.trakt.changes:
            log.debug('[%r, %r]', media, data)

            if data not in self.handlers:
                log.warn('Unknown sync data: %r', data)
                continue

            try:
                self.handlers[data].run(media, self.current.mode, changes)
            except Exception, ex:
                log.warn('Exception raised in handlers[%r].run(%r, ...): %s', data, media, ex, exc_info=True)

        # Flush caches to archives
        # self.current.state.flush()
