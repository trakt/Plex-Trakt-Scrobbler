from plugin.core.environment import Environment

import logging

log = logging.getLogger(__name__)


class SessionPrefix(object):
    @classmethod
    def get(cls):
        prefix = cls._get()

        # Initial
        if prefix is None:
            return cls.increment()

        return prefix

    @classmethod
    def increment(cls):
        prefix = Environment.dict['session.prefix']

        if prefix is None:
            prefix = 1
        else:
            prefix += 1

        # Update session prefix
        cls._set(prefix)

        log.debug('Incremented session prefix to %r', prefix)
        return prefix

    @classmethod
    def _get(cls):
        return Environment.dict['session.prefix']

    @classmethod
    def _set(cls, prefix):
        Environment.dict['session.prefix'] = prefix
