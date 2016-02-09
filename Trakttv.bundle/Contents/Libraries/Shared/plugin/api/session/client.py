from plugin.api.core.base import Service, expose
from plugin.managers.client import ClientManager
from plugin.managers.client_rule import ClientRuleManager

import logging

log = logging.getLogger(__name__)


class ClientService(Service):
    __key__ = 'session.client'

    @expose
    def list(self, full=False):
        return [
            client.to_json(full=full)
            for client in ClientManager.get.all()
        ]


class ClientRuleService(Service):
    __key__ = 'session.client.rule'

    @expose
    def list(self, full=False):
        return [
            rule.to_json(full=full)
            for rule in ClientRuleManager.get.all()
        ]

    @expose
    def update(self, current, full=False):
        result = []

        # Build array of current ids
        current_ids = [
            r.get('id')
            for r in current
            if r.get('id') is not None
        ]

        # Delete rules
        deleted_rules = [
            rule
            for rule in ClientRuleManager.get.all()
            if rule.id not in current_ids
        ]

        for rule in deleted_rules:
            rule.delete_instance()

            log.debug('Deleted %r', rule)

        # Create/Update client rules
        for r in current:
            id = r.pop('id', None)

            if id is None:
                # Create new rule
                rule = ClientRuleManager.create(**r)

                log.debug('Created %r', rule)
                result.append(rule)
                continue

            # Retrieve existing rule
            rule = ClientRuleManager.get(id=id)

            # Update rule
            ClientRuleManager.update(rule, r)

            log.debug('Updated %r', rule)
            result.append(rule)

        # Ensure result is sorted by priority
        result = sorted(result, key=lambda item: item.priority)

        # Convert rules to serializable dictionaries
        return [
            r.to_json(full=full)
            for r in result
        ]
