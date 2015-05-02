from plugin.managers.core.base import Manager
from plugin.models import ClientRule


class ClientRuleManager(Manager):
    model = ClientRule
