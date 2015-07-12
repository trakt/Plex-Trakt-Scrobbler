from plugin.api.core.base import Service, expose
from plugin.api.core.exceptions import ApiError
from plugin.managers import ClientRuleManager, UserRuleManager
import logging

log = logging.getLogger(__name__)


class UnknownTypeError(ApiError):
    code = 'rule.unknown_type'
    message = 'Unknown rule type provided'


class Rule(Service):
    __key__ = 'rule'

    @expose
    def list(self, type, full=False):
        if type == 'client':
            return [
                rule.to_json(full=full)
                for rule in ClientRuleManager.get.all()
            ]

        if type == 'user':
            return [
                rule.to_json(full=full)
                for rule in UserRuleManager.get.all()
            ]

        raise UnknownTypeError
