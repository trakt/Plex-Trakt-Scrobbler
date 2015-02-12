from plugin.core.helpers.variable import to_integer
from plugin.managers.core.base import Manager
from plugin.models import User

import logging

log = logging.getLogger(__name__)


class UserManager(Manager):
    model = User

    @classmethod
    def from_session(cls, session, fetch=False):
        if session.user.id is None:
            return None

        user_id = to_integer(session.user.id)

        return cls.get_or_create(
            session.user,

            User.id == user_id,

            fetch=fetch,
            on_create={
                'id': user_id
            }
        )

    @classmethod
    def to_dict(cls, user, fetch=False):
        return {
            'name': user.title,
            'thumb': user.thumb
        }
