from plugin.api.core.base import Service, expose
from plugin.preferences import OPTIONS_BY_KEY

import logging

log = logging.getLogger(__name__)


class Option(Service):
    __key__ = 'option'

    @expose
    def list(self, account=None):
        scope = 'account' if account is not None else 'server'

        def retrieve():
            for key, option in OPTIONS_BY_KEY.items():
                if option.scope != scope:
                    continue

                # Retrieve option details from database
                option = option.get(account)

                # Build option details
                data = {
                    'key': key,
                    'type': option.type,

                    'default': option.default,

                    'group': option.group,
                    'label': option.label,

                    'value': option.value
                }

                if option.type == 'enum':
                    data['choices'] = option.choices

                # Yield option
                yield data

        return list(retrieve())
