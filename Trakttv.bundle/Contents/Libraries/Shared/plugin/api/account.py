from plugin.api.core.base import Service, expose
from plugin.api.core.exceptions import ApiError
from plugin.managers import AccountManager

import apsw
import logging
import peewee
from plugin.managers.core.exceptions import TraktAccountExistsException, PlexAccountExistsException

log = logging.getLogger(__name__)


class TraktAccountExistsError(ApiError):
    code = 'account.trakt.account_exists'
    message = 'Trakt account is already in use'


class PlexAccountExistsError(ApiError):
    code = 'account.plex.account_exists'
    message = 'Plex account is already in use'


class NameConflictError(ApiError):
    code = 'account.name_conflict'
    message = 'Name conflicts with an existing account'


class UpdateFailedError(ApiError):
    code = 'account.update_failed'
    message = 'Unable to update account'


class Account(Service):
    __key__ = 'account'

    @expose
    def create(self, name):
        try:
            AccountManager.create(
                name=name
            )
        except (apsw.ConstraintError, peewee.IntegrityError):
            raise NameConflictError

        return True

    @expose
    def get(self, full=False, **kwargs):
        query = dict([
            (key, value)
            for (key, value) in kwargs.items()
            if key in ['id', 'username']
        ])

        if len(query) < 1:
            return None

        return AccountManager.get(**query).to_json(full=full)

    @expose
    def list(self, full=False):
        return [
            account.to_json(full=full)
            for account in AccountManager.get.all()
        ]

    @expose
    def update(self, id, data):
        # Retrieve current account
        account = AccountManager.get.by_id(id)

        try:
            # Update `account` with changes
            if not AccountManager.update.from_dict(account, data):
                raise UpdateFailedError
        except PlexAccountExistsException:
            # Raise as an API-safe error
            raise PlexAccountExistsError
        except TraktAccountExistsException:
            # Raise as an API-safe error
            raise TraktAccountExistsError

        # Return updated `account`
        return account.to_json(full=True)
