from plugin.core.helpers import decorator
from plugin.managers import AccountManager
from plugin.models import Account

import logging

log = logging.getLogger(__name__)


CONFIGURATION_HANDLERS = {}

@decorator.wraps
def handler(key=None):
    def outer(func):
        CONFIGURATION_HANDLERS[key or func.func_name] = func
        return func

    return outer


class Configuration(object):
    default = None
    handlers = CONFIGURATION_HANDLERS

    @classmethod
    def process(cls, key, value):
        if cls.default is None:
            cls.default = cls()

        if key not in cls.handlers:
            return False

        log.debug('Processing configuration change for %r', key)

        try:
            return cls.handlers[key](cls.default, value)
        except Exception, ex:
            log.warn('Unable to process configuration change for %r - %s', key, str(ex), exc_info=True)
            return False

    #
    # Handlers
    #

    @handler
    def pin(self, value):
        if not value:
            # Ignore empty PIN field
            return True

        # Retrieve administrator account
        account = AccountManager.get(Account.id == 1)

        # Update administrator authorization
        if not AccountManager.update.from_pin(account, value):
            log.warn('Unable to update account')
            return False

        return True
