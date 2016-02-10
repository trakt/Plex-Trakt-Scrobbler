from plugin.api.core.base import Service, expose
from plugin.managers.user import UserManager
from plugin.managers.user_rule import UserRuleManager

import logging

log = logging.getLogger(__name__)


class UserService(Service):
    __key__ = 'session.user'

    @expose
    def list(self, full=False):
        return [
            user.to_json(full=full)
            for user in UserManager.get.all()
        ]


class UserRuleService(Service):
    __key__ = 'session.user.rule'

    @expose
    def list(self, full=False):
        return [
            rule.to_json(full=full)
            for rule in UserRuleManager.get.all()
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
            for rule in UserRuleManager.get.all()
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
                rule = UserRuleManager.create(**r)

                log.debug('Created %r', rule)
                result.append(rule)
                continue

            # Retrieve existing rule
            rule = UserRuleManager.get(id=id)

            # Update rule
            UserRuleManager.update(rule, r)

            log.debug('Updated %r', rule)
            result.append(rule)

        # Ensure result is sorted by priority
        result = sorted(result, key=lambda item: item.priority)

        # Convert rules to serializable dictionaries
        return [
            r.to_json(full=full)
            for r in result
        ]
