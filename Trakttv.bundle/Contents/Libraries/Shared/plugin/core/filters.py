from plugin.core.environment import Environment
from plugin.core.helpers.variable import flatten

import ipaddress
import logging

log = logging.getLogger(__name__)


class Filters(object):
    @classmethod
    def get(cls, key, normalize_values=True):
        value = Environment.get_pref(key)
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
                value = cls.normalize(value)

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
        if value and normalize_values:
            value = cls.normalize(value)

        # Fetch filter
        f_allow, f_deny = cls.get(key, normalize_values=normalize_values)

        # Wildcard
        if f_allow is None and f_deny is None:
            log.debug('[%s] %r - wildcard', key, value)
            return True

        if f_transform:
            # Transform filter values
            f_allow = [f_transform(x) for x in f_allow]
            f_deny = [f_transform(x) for x in f_deny]

        log.debug('[%s] validate - value: %r, allow: %s, deny: %s', key, value, f_allow, f_deny)

        if f_validate(value, f_allow, f_deny):
            log.info('[%s] %r - filtered', key, value)
            return False

        return True

    @classmethod
    def normalize(cls, value):
        if type(value) is list:
            return [cls.normalize(v) for v in value]

        # Function option
        if value.startswith('#'):
            value = flatten(value)

            if value:
                return '#' + value

            return value

        # Basic option
        if value:
            value = value.strip()

        return flatten(value)

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
        log.debug('Filters.is_valid_client(%r)', player)

        def f_current():
            if not player:
                return None

            values = [player.get('title')]

            # Product
            product = player.get('product', '').lower()

            if product == 'dlna':
                values.append('#dlna')

            return values

        def f_validate(values, f_allow, f_deny):
            if f_allow:
                # Check if player details exist
                if not player:
                    return True

                # Check if player is allowed
                if not cls._contains_one(values, f_allow):
                    return True

            # Check if player is denied
            if cls._contains_one(values, f_deny):
                return True

            return False

        return cls.match(
            'scrobble_clients',
            f_current=f_current,
            f_validate=f_validate
        )

    @classmethod
    def is_valid_metadata_section(cls, metadata):
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
    def is_valid_section_name(cls, section_name):
        return cls.match(
            'filter_sections',
            f_current=lambda: section_name,
            f_validate=lambda value, f_allow, f_deny: (
                (f_allow and value not in f_allow) or
                value in f_deny
            ),
            f_check=lambda: (
                not section_name
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
            except ValueError:
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
            except ValueError:
                log.warn('validate "filter_networks" - unable to parse IP Network: %s', repr(value))
                return None

        return cls.match(
            'filter_networks',
            normalize_values=False,
            f_current=f_current,
            f_validate=f_validate,
            f_transform=f_transform
        )

    @classmethod
    def _contains_one(cls, values, f_items):
        for value in values:
            if value in f_items:
                return True

        return False
