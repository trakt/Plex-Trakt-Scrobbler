from plugin.api.core.base import Service, expose
from plugin.api.core.exceptions import ApiError
from plugin.managers import AccountManager

import apsw
import logging
import peewee

log = logging.getLogger(__name__)


class NameConflictError(ApiError):
    code = 'account.name_conflict'
    message = 'Name conflicts with an existing account'


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
        log.debug('update(%r, %r)', id, data)

        # Retrieve current account
        account = AccountManager.get.by_id(id)

        # Update `account` with changes
        if not AccountManager.update.from_dict(account, data):
            # Unable to update account
            return None

        # Return updated `account`
        return account.to_json(full=True)
