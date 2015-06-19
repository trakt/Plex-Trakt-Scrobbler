from plugin.preferences.options.core.base import Option
from plugin.sync.core.task.configuration.options import OPTIONS_BY_KEY

import logging

log = logging.getLogger(__name__)


class SyncOption(Option):
    def __init__(self):
        self.property = OPTIONS_BY_KEY.get(self.__database__)

        if self.property is None:
            log.warn('Unknown option: %r', self.__database__)
