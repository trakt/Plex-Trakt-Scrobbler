from plugin.core.environment import translate as _
from plugin.preferences.options.core.base import SimpleOption

import logging

log = logging.getLogger(__name__)


class ApiOption(SimpleOption):
    key = 'api.enabled'
    type = 'boolean'

    default = None
    scope = 'server'

    group = (_('API'),)
    label = _('Enabled')
    order = 200

    @property
    def value(self):
        value = super(ApiOption, self).value

        if value is None:
            return True

        return value
