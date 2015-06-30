from plugin.managers.core.base import Manager, Get
from plugin.models import UserRule


class GetUser(Get):
    def all(self):
        return super(GetUser, self).all() \
            .order_by(UserRule.priority.asc())


class UserRuleManager(Manager):
    get = GetUser

    model = UserRule
