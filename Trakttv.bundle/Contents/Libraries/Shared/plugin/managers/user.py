from plugin.core.helpers.variable import to_integer
from plugin.managers.core.base import Get, Manager, Update
from plugin.models import User, UserRule

import apsw
import logging

log = logging.getLogger(__name__)


class GetUser(Get):
    def __call__(self, user):
        user = self.manager.parse_user(user)

        return super(GetUser, self).__call__(
            User.id == to_integer(user['id'])
        )

    def or_create(self, user, fetch=False):
        user = self.manager.parse_user(user)

        try:
            # Create new user
            obj = self.manager.create(
                id=to_integer(user['id'])
            )

            # Update newly created object
            self.manager.update(obj, user, fetch)

            return obj
        except apsw.ConstraintError:
            # Return existing user
            return self(user)


class UpdateUser(Update):
    def __call__(self, obj, user, fetch=False):
        user = self.manager.parse_user(user)
        data = self.to_dict(obj, user, fetch)

        return super(UpdateUser, self).__call__(
            obj, data
        )

    def to_dict(self, obj, user, fetch=False):
        result = {}

        # Fill `result` with available fields
        if user.get('title'):
            result['name'] = user['title']

        if user.get('thumb'):
            result['thumb'] = user['thumb']

        if not fetch:
            # Return simple update
            return result

        # Find matching `UserRule`
        query = UserRule.select().where((
            (UserRule.name == user['title']) | (UserRule.name == None)
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

    @classmethod
    def parse_user(cls, user):
        if type(user) is dict:
            return user

        # Build user dict from object
        return {
            'id': user.id,
            'title': user.title,
            'thumb': user.thumb
        }
