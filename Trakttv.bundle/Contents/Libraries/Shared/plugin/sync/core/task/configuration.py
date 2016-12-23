from plugin.preferences import OPTIONS_BY_KEY

import elapsed
import logging

log = logging.getLogger(__name__)


class SyncConfiguration(object):
    def __init__(self, task):
        self.task = task

        self._options = {}

    @elapsed.clock
    def load(self, account):
        log.debug('Task Configuration:')

        # Load options from database
        for key, option in OPTIONS_BY_KEY.items():
            if option.scope == 'account':
                self._options[key] = option.get(account)
            elif option.scope == 'server':
                self._options[key] = option.get()

            log.debug(' - [%s]: %r', key, self._options[key].value)

    def keys(self):
        return self._options.keys()

    def __getitem__(self, key):
        return self._options[key].value
