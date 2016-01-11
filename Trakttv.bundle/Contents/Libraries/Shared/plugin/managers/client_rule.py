from plugin.managers.core.base import Manager, Get
from plugin.models import ClientRule


class GetClient(Get):
    def all(self):
        return super(GetClient, self).all()\
            .order_by(ClientRule.priority.asc())


class ClientRuleManager(Manager):
    get = GetClient

    model = ClientRule
