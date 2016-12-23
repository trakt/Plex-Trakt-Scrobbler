from plugin.core.filters import Filters
from plugin.core.helpers.variable import to_integer
from plugin.managers.core.base import Get, Manager, Update
from plugin.managers.core.exceptions import UserFilteredException
from plugin.models import User, UserRule, PlexAccount

from exception_wrappers.libraries import apsw
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

        filtered, data = self.to_dict(
            obj, user,

            fetch=fetch,
            match=match
        )

        updated = super(UpdateUser, self).__call__(
            obj, data
        )

        if filtered and filtered_exception:
            raise UserFilteredException

        return updated

    def to_dict(self, obj, user, fetch=False, match=False):
        result = {}

        # Fill `result` with available fields
        if user.get('title'):
            result['name'] = user['title']

        if user.get('thumb'):
            result['thumb'] = user['thumb']

        filtered = False

        if match:
            # Try match `User` against rules
            filtered, result = self.match(
                result, user
            )

        return filtered, result

    @classmethod
    def match(cls, result, user):
        # Apply global filters
        if not Filters.is_valid_user(user):
            # User didn't pass filters, update `account` attribute and return
            result['account'] = None

            return True, result

        # Find matching `UserRule`
        rule = (UserRule
            .select()
            .where(
                (UserRule.name == user['title']) |
                (UserRule.name == '*') |
                (UserRule.name == None)
            )
            .order_by(
                UserRule.priority.asc()
            )
            .first()
        )

        log.debug('Activity matched against rule: %r', rule)

        if rule:
            # Process rule
            if rule.account_function is not None:
                result['account'] = cls.account_function(user, rule)
            elif rule.account_id is not None:
                result['account'] = rule.account_id
            else:
                return True, result
        else:
            result['account'] = None

        return False, result

    @staticmethod
    def account_function(user, rule):
        func = rule.account_function

        # Handle account function
        account_id = None

        if func == '@':
            # Map, try automatically finding matching `PlexAccount`
            plex_account = (PlexAccount
                .select()
                .where(
                    (PlexAccount.username == user['title']) |
                    (PlexAccount.title == user['title'])
                )
                .first()
            )

            if plex_account:
                account_id = plex_account.account_id
        else:
            log.warn('Unknown account function: %r', func)
            return None

        # Ensure `account_id` is valid
        if account_id is None:
            log.info('Unable to match user %r against any account', user['title'])
            return None

        log.debug('Matched user %r to account %r', user['title'], account_id)
        return account_id


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
