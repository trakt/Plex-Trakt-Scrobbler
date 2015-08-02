from plugin.preferences.options.core.base import SimpleOption

import logging

log = logging.getLogger(__name__)


class ApiOption(SimpleOption):
    key = 'api.enabled'
    type = 'boolean'

    default = None
    scope = 'server'

    group = ('API',)
    label = 'Enabled'
    order = 200

    @property
    def value(self):
        value = super(ApiOption, self).value

        if value is None:
            return True

        return value
