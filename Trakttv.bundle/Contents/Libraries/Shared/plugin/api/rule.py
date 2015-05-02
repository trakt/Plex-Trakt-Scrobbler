from plugin.api.core.base import Service, expose
from plugin.managers import ClientRuleManager, UserRuleManager
import logging

log = logging.getLogger(__name__)


class Rule(Service):
    __key__ = 'rule'

    @expose
    def list(self, full=False):
        return {
            'client': [
                rule.to_json(full=full)
                for rule in ClientRuleManager.get.all()
            ],
            'user': [
                rule.to_json(full=full)
                for rule in UserRuleManager.get.all()
            ]
        }
