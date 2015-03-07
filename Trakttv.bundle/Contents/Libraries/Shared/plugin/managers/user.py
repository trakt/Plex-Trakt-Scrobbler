from plugin.core.helpers.variable import to_integer
from plugin.managers.core.base import Get, Manager, Update
from plugin.models import User, UserRule

import apsw
import logging

log = logging.getLogger(__name__)


class GetUser(Get):
    def __call__(self, user):
        return super(GetUser, self).__call__(
            User.id == to_integer(user.id)
        )

    def or_create(self, user, fetch=False):
        try:
            # Create new user
            obj = self.manager.create(
                id=to_integer(user.id)
            )

            # Update newly created object
            self.manager.update(obj, user, fetch)

            return obj
        except apsw.ConstraintError:
            # Return existing user
            return self(user)


class UpdateUser(Update):
    def __call__(self, obj, user, fetch=False):
        data = self.to_dict(obj, user, fetch)

        return super(UpdateUser, self).__call__(
            obj, data
        )

    def to_dict(self, obj, user, fetch=False):
        result = {
            'name': user.title,
            'thumb': user.thumb
        }

        if not fetch:
            # Return simple update
            return result

        # Find matching `UserRule`
        query = UserRule.select().where((
            (UserRule.name == user.title) | (UserRule.name == None)
        ))

        rules = list(query.execute())

        if len(rules) != 1:
            return result

        result['account'] = rules[0].account_id

        return result


class UserManager(Manager):
    get = GetUser
    update = UpdateUser

    model = User
