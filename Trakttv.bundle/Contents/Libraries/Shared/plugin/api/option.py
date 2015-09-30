from plugin.api.core.base import Service, expose
from plugin.api.core.exceptions import ApiError
from plugin.preferences import OPTIONS_BY_KEY

import logging

log = logging.getLogger(__name__)


class InvalidScopeError(ApiError):
    code = 'option.invalid_scope'
    message = "Option doesn't match the current scope"


class InvalidUpdateError(ApiError):
    code = 'option.invalid_update'
    message = "Received an invalid update request"


class UnknownOptionError(ApiError):
    code = 'option.unknown_option'
    message = "Unknown option referenced"


class UpdateConflictError(ApiError):
    code = 'option.update_conflict'
    message = "Update conflict, options have been changed by another user"


class OptionService(Service):
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

                # Convert option to dictionary
                yield option.to_dict()

        return list(retrieve())

    @expose
    def update(self, changes, account=None):
        scope = 'account' if account is not None else 'server'

        # Validate changes
        changed = {}
        ignored = []

        for key, change in changes.items():
            if 'from' not in change or 'to' not in change:
                raise InvalidUpdateError

            if key not in OPTIONS_BY_KEY:
                raise UnknownOptionError
            # Retrieve option
            option = OPTIONS_BY_KEY[key]

            if option.scope != scope:
                raise InvalidScopeError

            # Retrieve option details from database
            option = option.get(account)

            if option.value != change['from']:
                raise UpdateConflictError

            # Ensure option has changed
            if change['from'] == change['to']:
                ignored.append(key)
                continue

            changed[key] = change

        # Update options
        updated = []

        for key, change in changed.items():
            if key not in OPTIONS_BY_KEY:
                raise UnknownOptionError

            value = change['to']

            # Update value
            option = OPTIONS_BY_KEY[key]
            option.update(value, account)

            updated.append(key)

        return {
            'updated': updated,
            'ignored': ignored
        }
