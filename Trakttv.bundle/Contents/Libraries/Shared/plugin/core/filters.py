from plugin.core.environment import Environment
from plugin.core.helpers.variable import flatten, get_pref

import ipaddress
import logging

log = logging.getLogger(__name__)


class Filters(object):
    @staticmethod
    def get(key, normalize_values=True):
        value = get_pref(key)
        if not value:
            return None, None

        value = value.strip()

        # Allow all if wildcard (*) or blank
        if not value or value == '*':
            return None, None

        values = value.split(',')

        allow, deny = [], []

        for value in [v.strip() for v in values]:
            inverted = False

            # Check if this is an inverted value
            if value.startswith('-'):
                inverted = True
                value = value[1:]

            # Normalize values (if enabled)
            if normalize_values:
                value = flatten(value)

            # Append value to list
            if not inverted:
                allow.append(value)
            else:
                deny.append(value)

        return allow, deny

    @classmethod
    def match(cls, key, f_current, f_validate, f_check=None, f_transform=None, normalize_values=True):
        if Environment.prefs[key] is None:
            log.debug('[%s] no preference found', key)
            return True

        if f_check and f_check():
            return True

        value = f_current()

        # Normalize value
        if normalize_values:
            if value:
                value = value.strip()

            value = flatten(value)

        # Fetch filter
        f_allow, f_deny = cls.get(key, normalize_values=normalize_values)

        # Wildcard
        if f_allow is None and f_deny is None:
            log.debug('[%s] wildcard', key)
            return True

        if f_transform:
            # Transform filter values
            f_allow = [f_transform(x) for x in f_allow]
            f_deny = [f_transform(x) for x in f_deny]

        log.debug('[%s] validate - value: %s, allow: %s, deny: %s', key, repr(value), f_allow, f_deny)

        if f_validate(value, f_allow, f_deny):
            log.info('[%s] filtered %r' % (
                key, f_current()
            ))
            return False

        return True

    @classmethod
    def is_valid_user(cls, user):
        return cls.match(
            'scrobble_names',
            f_current=lambda: user.get('title') if user else None,
            f_validate=lambda value, f_allow, f_deny: (
                (f_allow and (
                    not user or
                    value not in f_allow
                )) or
                value in f_deny
            )
        )

    @classmethod
    def is_valid_client(cls, player):
        return cls.match(
            'scrobble_clients',
            f_current=lambda: player.get('title') if player else None,
            f_validate=lambda value, f_allow, f_deny: (
                (f_allow and (
                    not player or
                    value not in f_allow
                )) or
                value in f_deny
            )
        )

    @classmethod
    def is_valid_section(cls, metadata):
        return cls.match(
            'filter_sections',
            f_current=lambda: metadata.section.title,
            f_validate=lambda value, f_allow, f_deny: (
                (f_allow and value not in f_allow) or
                value in f_deny
            ),
            f_check=lambda: (
                not metadata or
                not metadata.section.title
            )
        )

    @classmethod
    def is_valid_address(cls, client):
        def f_current():
            if not client or not client['address']:
                return None

            value = client['address']

            try:
                return ipaddress.ip_address(unicode(value))
            except ValueError, ex:
                log.warn('validate "filter_networks" - unable to parse IP Address: %s', repr(value))
                return None

        def f_validate(value, f_allow, f_deny):
            if not value:
                return True

            allowed = any([
                value in network
                for network in f_allow
                if network is not None
            ])

            denied = any([
                 value in network
                 for network in f_deny
                 if network is not None
             ])

            return not allowed or denied

        def f_transform(value):
            if not value:
                return None

            try:
                return ipaddress.ip_network(unicode(value))
            except ValueError, ex:
                log.warn('validate "filter_networks" - unable to parse IP Network: %s', repr(value))
                return None

        return cls.match(
            'filter_networks',
            normalize_values=False,
            f_current=f_current,
            f_validate=f_validate,
            f_transform=f_transform
        )
