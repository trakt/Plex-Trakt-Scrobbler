from plugin.core.filters import Filters
from plugin.core.helpers.variable import to_integer
from plugin.managers.core.base import Get, Manager, Update
from plugin.managers.core.exceptions import UserFilteredException
from plugin.models import User, UserRule

import apsw
import logging
import peewee

log = logging.getLogger(__name__)


class GetUser(Get):
    def __call__(self, user):
        user = self.manager.parse_user(user)

        if not user:
            return None

        return super(GetUser, self).__call__(
            User.key == to_integer(user['key'])
        )

    def or_create(self, user, fetch=False, match=False, filtered_exception=False):
        user = self.manager.parse_user(user)

        if not user:
            return None

        try:
            # Create new user
            obj = self.manager.create(
                key=to_integer(user['key'])
            )

            # Update newly created object
            self.manager.update(
                obj, user,

                fetch=fetch,
                match=match,
                filtered_exception=filtered_exception
            )

            return obj
        except (apsw.ConstraintError, peewee.IntegrityError):
            # Return existing user
            obj = self(user)

            if fetch or match:
                # Update existing `User`
                self.manager.update(
                    obj, user,

                    fetch=fetch,
                    match=match,
                    filtered_exception=filtered_exception
                )

            return obj


class UpdateUser(Update):
    def __call__(self, obj, user, fetch=False, match=False, filtered_exception=False):
        user = self.manager.parse_user(user)

        if not user:
            return None

        data = self.to_dict(
            obj, user,

            fetch=fetch,
            match=match,
            filtered_exception=filtered_exception
        )

        return super(UpdateUser, self).__call__(
            obj, data
        )

    def to_dict(self, obj, user, fetch=False, match=False, filtered_exception=False):
        result = {}

        # Fill `result` with available fields
        if user.get('title'):
            result['name'] = user['title']

        if user.get('thumb'):
            result['thumb'] = user['thumb']

        if match:
            # Try match `User` against rules
            result = self.match(
                result, user,
                filtered_exception=filtered_exception
            )

        return result

    @staticmethod
    def match(result, user, filtered_exception=False):
        # Apply global filters
        if not Filters.is_valid_user(user):
            # User didn't pass filters, update `account` attribute and return
            result['account'] = None

            if filtered_exception:
                raise UserFilteredException

            return result

        # Find matching `UserRule`
        query = UserRule.select().where((
            (UserRule.name == user['title']) | (UserRule.name == None)
        ))

        rules = list(query.execute())

        if len(rules) == 1:
            result['account'] = rules[0].account_id
        else:
            result['account'] = None

        return result


class UserManager(Manager):
    get = GetUser
    update = UpdateUser

    model = User

    @classmethod
    def parse_user(cls, user):
        if type(user) is not dict:
            # Build user dict from object
            user = {
                'key': user.id,
                'title': user.title,
                'thumb': user.thumb
            }

        # Validate `user`
        if not user.get('key'):
            return None

        return user
