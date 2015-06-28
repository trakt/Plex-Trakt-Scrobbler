from plugin.preferences.options.core.base import Option

import logging

log = logging.getLogger(__name__)


class ApiOption(Option):
    key = 'api.enabled'
    type = 'boolean'

    default = None
    scope = 'server'

    group = ('API',)
    label = 'Enabled'

    @property
    def value(self):
        value = super(ApiOption, self).value

        if value is None:
            return False

        return value
